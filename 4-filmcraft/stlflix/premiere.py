"""Kit STLFLIX com o Premiere Pro no lugar do FilmCraft (versão do fork EduardoZFerreira/STLFLIX_EDITOR_FOR_PREMIERE).

O Python não fala com o Premiere. Quem opera o Premiere é o Claude, pelo conector MCP (ferramentas mcp__premiere-pro__*).
A troca entre os dois é por arquivos:

- Premiere → kit: o Claude exporta a sequência em XML (FCP7) com `export_as_fcp_xml` e o áudio em WAV com
  `export_sequence`; os comandos daqui leem esses arquivos (cortes, fps, tamanho, trilhas, caminhos da mídia).
- kit → Premiere: a decupagem vira um XML (FCP7) que o Claude importa com `import_fcp_xml` (mode into_open_project),
  como uma sequência NOVA; os motions viram uma lista JSON que o Claude coloca com o conector.

    premiere.cmd --projeto <VSL> decupar <seq> --ref <sequencia.xml> [--escala 50] [--nome "Corpo decupado"]
    premiere.cmd --projeto <VSL> conferir <seq> [--plano arquivo] [--fps 29.97]
    premiere.cmd --projeto <VSL> transcrever <seq> --xml <sequencia.xml> --wav <mix.wav>
    premiere.cmd --projeto <VSL> motions <seq> --ref <sequencia.xml> [--plano arquivo]
    premiere.cmd --projeto <VSL> checar --xml <sequencia.xml> [--xml outra.xml]
    premiere.cmd --projeto <VSL> entregar-xml <arquivo.xml>... [--destino pasta]

Tempo: o Premiere usa os mesmos 254.016.000.000 ticks por segundo do FilmCraft.
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from . import blocos, decupagem, motions, vsls
from .audio import trechos_mudos
from .projeto import Projeto
from .tempo import T, mmss, tc

_PALAVRAS = {}                                   # id(máscara de fala) -> palavras do take (para o refinar achar a palavra do corte)
_energia_original = decupagem.energia


def _energia_com_palavras(wav):
    r = _energia_original(wav)
    js = os.path.splitext(wav)[0] + ".json"
    if os.path.exists(js):
        _PALAVRAS[id(r[0])] = json.load(open(js, encoding="utf-8"))["words"]
    return r


def refinar_sem_cortar_palavra(md, a, b, quadro_fps):
    """Troca o `decupagem.refinar` do kit: o corte acompanha a palavra, não o tempo do Whisper.

    O Whisper marca o fim das palavras cedo, e o refinar original travava o clipe nesse fim (min(b, …)): a última
    palavra saía cortada ao meio. Aqui, o fim vai até o fim real da última palavra do trecho (anda enquanto houver
    fala, sem entrar na palavra seguinte) e o começo volta até o início real da primeira palavra (sem entrar na
    palavra anterior)."""
    import numpy as np
    fala, db = md
    pal = _PALAVRAS.get(id(fala), [])
    n = len(fala)
    avisos = []
    ia, ib = int(round(a * 100)), int(round(b * 100))
    if fala[ia:ia + 3].any():                                  # começo no meio da fala
        ant = [w for w in pal if w["start"] < a - 0.02]
        piso = max(ia - 40, int(round(ant[-1]["end"] * 100))) if ant else max(0, ia - 40)
        k = ia
        while k > piso and fala[max(0, k - 3):k].any():
            k -= 1
        if k != ia:
            avisos.append(f"o começo caía na fala: movido de {mmss(a)} para {mmss(k / 100)}")
        a, ia = k / 100, k
    if fala[max(0, ib - 3):ib + 3].any():                      # fim no meio da fala
        dentro = [w for w in pal if w["start"] <= b - 0.02]
        prox = [w for w in pal if w["start"] > b - 0.02]
        teto = min(n, ib + 100)
        if prox:
            teto = min(teto, int(round(prox[0]["start"] * 100)) - 3)
        ult_fim = int(round(dentro[-1]["end"] * 100)) if dentro else ib
        k = max(ib, min(ult_fim, teto))
        while k < teto and fala[k:k + 4].any():
            k += 1
        if k != ib:
            avisos.append(f"o fim caía na fala: movido de {mmss(b)} para {mmss(k / 100)}")
        b, ib = k / 100, k
    b_lim = b + decupagem.CAUDA_Q / quadro_fps
    seguinte = [w for w in pal if w["start"] > b - 0.02]
    if seguinte:                                              # a cauda não entra na palavra seguinte
        b_lim = min(b_lim, max(b, seguinte[0]["start"] - 0.02))
    idx = np.flatnonzero(fala[ia:ib])
    if idx.size == 0:
        return [], ["sem fala no trecho"]
    ilhas, s0, ant = [], idx[0], idx[0]
    for k in idx[1:]:
        if (k - ant) / 100 >= 0.10:
            ilhas.append((s0, ant + 1))
            s0 = k
        ant = k
    ilhas.append((s0, ant + 1))
    ilhas = [(ia + x, ia + y) for x, y in ilhas if y - x >= 6]
    clipes = []
    for on, off in ilhas:
        ini = max(a, on / 100 - decupagem.CABECA_Q / quadro_fps)
        fim = min(b_lim, off / 100 + decupagem.CAUDA_Q / quadro_fps)
        if clipes and ini - clipes[-1][1] < decupagem.PAUSA_MIN:
            clipes[-1] = (clipes[-1][0], fim)
        else:
            clipes.append((ini, fim))
    return clipes, avisos


decupagem.energia = _energia_com_palavras
decupagem.refinar = refinar_sem_cortar_palavra


CROSSFADE = ("Cross Fade (+3dB)", "KGAudioTransCrossFade3dB")      # o Constant Power do Premiere

# rótulos de cor do Premiere (nomes em inglês, como no XML que ele exporta); cada seção da decupagem ganha um
CORES_PREMIERE = ["Violet", "Iris", "Caribbean", "Lavender", "Cerulean", "Forest", "Rose", "Mango", "Purple", "Blue",
                  "Teal", "Magenta", "Tan", "Green", "Brown", "Yellow"]
COR_NA_SECAO = re.compile(r"\s*\[cor:\s*([A-Za-z]+)\s*\]\s*$", re.I)


def secao_e_cor(titulo):
    """'Lead · Versão A [cor: Rose]' → ('Lead · Versão A', 'Rose'); sem [cor: …] → (título, None)."""
    m = COR_NA_SECAO.search(titulo or "")
    if not m:
        return titulo, None
    nome = next((c for c in CORES_PREMIERE if c.lower() == m.group(1).lower()), None)
    if nome is None:
        raise ValueError(f"cor '{m.group(1)}' não existe no Premiere (use: {', '.join(CORES_PREMIERE)})")
    return titulo[:m.start()], nome


# ───── fps e quadros ─────

class Taxa:
    """Taxa de quadros no jeito do XML: timebase inteiro + NTSC (29,97 = 30 NTSC; 23,976 = 24 NTSC)."""

    def __init__(self, timebase, ntsc):
        self.timebase, self.ntsc = int(timebase), bool(ntsc)
        self.fps = self.timebase * 1000 / 1001 if self.ntsc else float(self.timebase)
        self.quadro = round(T * 1001 / (self.timebase * 1000)) if self.ntsc else round(T / self.timebase)

    @classmethod
    def de_fps(cls, fps):
        fps = float(fps)
        tb = round(fps)
        return cls(tb, abs(fps - tb) > 0.01)

    def xml(self):
        return f"<rate><timebase>{self.timebase}</timebase><ntsc>{'TRUE' if self.ntsc else 'FALSE'}</ntsc></rate>"


def _taxa_de(el):
    r = el.find("rate")
    return Taxa(r.findtext("timebase"), (r.findtext("ntsc") or "").upper() == "TRUE")


# ───── ler o XML exportado pelo Premiere ─────

def _caminho(pathurl):
    p = urllib.parse.unquote(pathurl or "")
    for pre in ("file://localhost/", "file:///", "file://"):
        if p.startswith(pre):
            p = p[len(pre):]
            break
    return os.path.normpath(p) if p else ""


def ler_xml(caminho, nome=None):
    """A sequência do XML (a principal, ou a de nome `nome`) em segundos:
    {nome, taxa, largura, altura, duracao, video: [trilha], audio: [trilha]}; trilha = {nome, ligada, itens}
    e item = {nome, inicio, fim, entrada, saida, caminho, ligado}."""
    raiz = ET.parse(caminho).getroot()
    seqs = [s for s in raiz.iter("sequence") if s.find("media") is not None]
    if not seqs:
        raise ValueError(f"nenhuma sequência no XML: {caminho}")
    principal = raiz.find("sequence")
    seq = next((s for s in seqs if s.findtext("name") == nome), None) if nome else (principal if principal is not None else seqs[0])
    if seq is None:
        raise KeyError(f"a sequência '{nome}' não está no XML (tem: {', '.join(s.findtext('name') or '?' for s in seqs)})")
    taxa = _taxa_de(seq)
    fmt = seq.find("media/video/format/samplecharacteristics")
    arquivos = {}
    for f in seq.iter("file"):                              # o 1º <file id> traz o caminho; os outros só a referência
        if f.find("pathurl") is not None:
            arquivos[f.get("id")] = _caminho(f.findtext("pathurl"))

    def trilhas(tipo):
        out = []
        for k, t in enumerate(seq.findall(f"media/{tipo}/track"), 1):
            # start/end = -1: o clipe passa por baixo de uma transição; o limite dele é o ponto de corte da transição
            itens, sem_fim, trans = [], [], None           # trans = (início da transição, ponto de corte)
            for el in t:
                if el.tag == "transitionitem":
                    a_, b_ = int(el.findtext("start")), int(el.findtext("end"))
                    cp = el.findtext("cutPointTicks")
                    trans = (a_, a_ + round(int(cp) / taxa.quadro) if cp else (a_ + b_) // 2)
                    for c in sem_fim:
                        c["fim_q"] = trans[1]
                    sem_fim = []
                    continue
                if el.tag != "clipitem":
                    continue
                ini, fim = int(el.findtext("start")), int(el.findtext("end"))
                ent, sai = int(el.findtext("in")), int(el.findtext("out"))
                arq = el.find("file")
                item = dict(nome=el.findtext("name") or "", ini_q=ini, fim_q=fim, ent_q=ent, sai_q=sai,
                            caminho=arquivos.get(arq.get("id"), "") if arq is not None else "",
                            ligado=(el.findtext("enabled") or "TRUE").upper() == "TRUE",
                            aninhada=el.find("sequence") is not None)
                if ini < 0:                                 # a entrada no bruto anda junto até o ponto de corte
                    tr_ini, corte = trans or (0, 0)
                    item["ini_q"], item["ent_q"] = corte, ent + (corte - tr_ini)
                if fim < 0:
                    sem_fim.append(item)
                trans = None
                itens.append(item)
            for c in sem_fim:                               # sem transição depois: pela duração no bruto
                c["fim_q"] = c["ini_q"] + (c["sai_q"] - c["ent_q"])
            for c in itens:
                c.update(inicio=c["ini_q"] / taxa.fps, fim=c["fim_q"] / taxa.fps, entrada=c["ent_q"] / taxa.fps)
            nome_t = f"{'Video' if tipo == 'video' else 'Audio'} {k}"
            out.append(dict(nome=nome_t, ligada=(t.findtext("enabled") or "TRUE").upper() == "TRUE", itens=itens,
                            estereo_par=t.get("currentExplodedTrackIndex")))
        return out

    video, audio = trilhas("video"), trilhas("audio")
    fim = max((c["fim"] for t in video + audio for c in t["itens"]), default=0.0)
    return dict(nome=seq.findtext("name") or "", taxa=taxa, fps=taxa.fps,
                largura=int(fmt.findtext("width")) if fmt is not None else None,
                altura=int(fmt.findtext("height")) if fmt is not None else None,
                duracao=fim, video=video, audio=audio)


def mapa_de_cortes(sx):
    """Mesmo formato do audio.mapa_de_cortes do kit, a partir do XML: os cortes da V1 (ou da A1, se a V1 estiver vazia)."""
    v1 = [c for c in (sx["video"][0]["itens"] if sx["video"] else []) if c["ligado"]]
    a1 = [c for c in (sx["audio"][0]["itens"] if sx["audio"] else []) if c["ligado"]]
    base = sorted(v1 or a1, key=lambda c: c["inicio"])
    cortes = [dict(start=c["inicio"], dur=c["fim"] - c["inicio"], take=c["nome"], src_in=c["entrada"]) for c in base]
    return dict(sequencia=sx["nome"], duracao=sx["duracao"], cortes=cortes)


# ───── decupagem → XML que o Premiere importa ─────

def _sonda(caminho):
    """(fps, duração s, largura, altura, canais de áudio, taxa de amostragem) do bruto, pelo ffprobe."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,r_frame_rate,width,height,channels,sample_rate:format=duration",
                        "-of", "json", caminho], capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), {})
    num, _, den = (v.get("r_frame_rate") or "24000/1001").partition("/")
    return dict(fps=float(num) / float(den or 1), dur=float(d.get("format", {}).get("duration") or 0),
                largura=v.get("width"), altura=v.get("height"), canais=int(a.get("channels") or 0),
                amostragem=int(a.get("sample_rate") or 48000))


def _url(caminho):
    p = os.path.abspath(caminho).replace("\\", "/")
    return "file://localhost/" + urllib.parse.quote(p, safe="/:[]")


def montar_xml(proj, chave, taxa, largura, altura, nome_seq, arquivo=None, escala=None):
    """Planeja a decupagem (as mesmas regras do kit: cabeça 2 q, cauda 5,5 q, pausas ≥ 0,3 s, crossfade 3/10 q) e
    devolve (xml, resumo). Os tempos saem em quadros da sequência e em pproTicks exatos."""
    clipes, trechos, erros = decupagem.planejar(proj, chave, arquivo, taxa.fps)
    if erros:
        raise ValueError("a decupagem tem erros: " + "; ".join(erros[:5]))
    conhecidos = json.load(open(os.path.join(decupagem.pasta_brutos(proj), "takes.json"), encoding="utf-8"))
    takes = {}
    for c in clipes:
        if c["take"] not in takes:
            if c["take"] not in conhecidos or not os.path.exists(conhecidos[c["take"]]["path"]):
                raise FileNotFoundError(f"não achei o arquivo do {c['take']} (rode transcrever-brutos de novo com --pasta)")
            p = conhecidos[c["take"]]["path"]
            takes[c["take"]] = dict(caminho=p, nome=os.path.basename(p), id=f"file-{len(takes) + 1}", **_sonda(p))

    # posição de cada clipe na timeline (quadros da sequência), como no aplicar() do kit
    pos, colocados = 0, []
    for c in clipes:
        q_in, q_out = round(c["a"] * taxa.fps), round(c["b"] * taxa.fps)
        n = q_out - q_in
        # pproTicksIn no mesmo quadro do <in>: o Premiere usa os ticks no áudio e o quadro no vídeo (senão o áudio desliza)
        colocados.append(dict(c, ini=pos, fim=pos + n, ent=q_in, sai=q_out, ent_t=q_in * taxa.quadro))
        pos += n

    # crossfade de áudio nos cortes encostados: centrado no corte, com as "alças" saindo do próprio bruto
    xfs = {}
    for k, (c, prox) in enumerate(zip(colocados, colocados[1:])):
        xf = c.get("xf")
        if not xf:
            continue
        meia = xf // 2
        if c["sai"] + (xf - meia) > round(takes[c["take"]]["dur"] * taxa.fps) or prox["ent"] - meia < 0:
            continue                                       # sem material sobrando no bruto para a transição
        xfs[k] = dict(ini=c["fim"] - meia, fim=c["fim"] - meia + xf, meia=meia, xf=xf)

    def arquivo_xml(tk, primeiro):
        t = takes[tk]
        if not primeiro:
            return f'<file id="{t["id"]}"/>'
        st = Taxa.de_fps(t["fps"])
        audio = (f"<audio><samplecharacteristics><depth>16</depth><samplerate>{t['amostragem']}</samplerate>"
                 f"</samplecharacteristics><channelcount>{t['canais']}</channelcount></audio>") if t["canais"] else ""
        return (f'<file id="{t["id"]}"><name>{escape(t["nome"])}</name><pathurl>{escape(_url(t["caminho"]))}</pathurl>'
                f'{st.xml()}<duration>{round(t["dur"] * st.fps)}</duration><media><video><samplecharacteristics>'
                f'{st.xml()}<width>{t["largura"]}</width><height>{t["altura"]}</height><anamorphic>FALSE</anamorphic>'
                f'<pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance></samplecharacteristics>'
                f'</video>{audio}</media></file>')

    canais = max((t["canais"] for t in takes.values()), default=0)
    trilhas_a = 2 if canais >= 2 else (1 if canais else 0)
    filtro = ""
    if escala is not None:
        filtro = (f"<filter><effect><name>Basic Motion</name><effectid>basic</effectid><effectcategory>motion</effectcategory>"
                  f"<effecttype>motion</effecttype><mediatype>video</mediatype><parameter authoringApp=\"PremierePro\">"
                  f"<parameterid>scale</parameterid><name>Scale</name><valuemin>0</valuemin><valuemax>1000</valuemax>"
                  f"<value>{float(escala):g}</value></parameter></effect></filter>")
    cores, livres = {}, [x for x in CORES_PREMIERE]        # cor de cada seção: a pedida no título ou a próxima livre
    for c in colocados:
        nome_s, pedida = secao_e_cor(c["trecho"]["bloco"])
        if nome_s not in cores and pedida:
            cores[nome_s] = pedida
    livres = [x for x in livres if x not in cores.values()]
    for c in colocados:
        nome_s, _ = secao_e_cor(c["trecho"]["bloco"])
        if nome_s not in cores:
            cores[nome_s] = livres.pop(0) if livres else "Violet"
        c["secao"], c["cor"] = nome_s, cores[nome_s]

    vistos, v_itens, a_itens = set(), [], [[] for _ in range(trilhas_a)]
    for k, c in enumerate(colocados):
        rotulo = f"<labels><label2>{c['cor']}</label2></labels>"
        n = c["fim"] - c["ini"]
        ids = [f"clipitem-v{k + 1}"] + [f"clipitem-a{j + 1}-{k + 1}" for j in range(trilhas_a)]
        links = (f"<link><linkclipref>{ids[0]}</linkclipref><mediatype>video</mediatype><trackindex>1</trackindex>"
                 f"<clipindex>{k + 1}</clipindex></link>"
                 + "".join(f"<link><linkclipref>{ids[j + 1]}</linkclipref><mediatype>audio</mediatype><trackindex>{j + 1}"
                           f"</trackindex><clipindex>{k + 1}</clipindex><groupindex>1</groupindex></link>" for j in range(trilhas_a)))
        dur_q = round(takes[c["take"]]["dur"] * taxa.fps)
        nome = escape(takes[c["take"]]["nome"])
        primeiro = c["take"] not in vistos
        vistos.add(c["take"])
        v_itens.append(f'<clipitem id="{ids[0]}"><masterclipid>masterclip-{c["take"]}</masterclipid><name>{nome}</name>'
                       f'<enabled>TRUE</enabled><duration>{dur_q}</duration>{taxa.xml()}<start>{c["ini"]}</start>'
                       f'<end>{c["fim"]}</end><in>{c["ent"]}</in><out>{c["sai"]}</out><pproTicksIn>{c["ent_t"]}</pproTicksIn>'
                       f'<pproTicksOut>{c["ent_t"] + n * taxa.quadro}</pproTicksOut><alphatype>none</alphatype>'
                       f'<pixelaspectratio>square</pixelaspectratio><anamorphic>FALSE</anamorphic>'
                       f'{arquivo_xml(c["take"], primeiro)}{filtro}{links}{rotulo}</clipitem>')
        # áudio: com crossfade, o clipe se estende sob a transição (end/start = -1, como o Premiere exporta)
        antes, depois = xfs.get(k - 1), xfs.get(k)
        ini, ent = (-1, c["ent"] - antes["meia"]) if antes else (c["ini"], c["ent"])
        fim, sai = (-1, c["sai"] + depois["xf"] - depois["meia"]) if depois else (c["fim"], c["sai"])
        t_in = c["ent_t"] - (antes["meia"] * taxa.quadro if antes else 0)
        t_out = c["ent_t"] + n * taxa.quadro + ((depois["xf"] - depois["meia"]) * taxa.quadro if depois else 0)
        for j in range(trilhas_a):
            tipo = ' premiereChannelType="stereo"' if trilhas_a == 2 else ""
            a_itens[j].append(f'<clipitem id="{ids[j + 1]}"{tipo}><masterclipid>masterclip-{c["take"]}</masterclipid>'
                              f'<name>{nome}</name><enabled>TRUE</enabled><duration>{dur_q}</duration>{taxa.xml()}'
                              f'<start>{ini}</start><end>{fim}</end><in>{ent}</in><out>{sai}</out>'
                              f'<pproTicksIn>{t_in}</pproTicksIn><pproTicksOut>{t_out}</pproTicksOut>'
                              f'<file id="{takes[c["take"]]["id"]}"/><sourcetrack><mediatype>audio</mediatype>'
                              f'<trackindex>{j + 1}</trackindex></sourcetrack>{links}{rotulo}</clipitem>')
            if depois:
                x = depois
                a_itens[j].append(f'<transitionitem><start>{x["ini"]}</start><end>{x["fim"]}</end>'
                                  f'<alignment>center</alignment><cutPointTicks>{x["meia"] * taxa.quadro}</cutPointTicks>'
                                  f'{taxa.xml()}<effect><name>{CROSSFADE[0]}</name><effectid>{CROSSFADE[1]}</effectid>'
                                  f'<effecttype>transition</effecttype><mediatype>audio</mediatype></effect></transitionitem>')

    # marcadores na sequência: início de cada bloco, "Conferir" e ideias de tela (TELA: …)
    marcadores, bloco = [], None
    for c in colocados:
        t = c["trecho"]
        if c["primeiro"]:
            if t["bloco"] and t["bloco"] != bloco:
                bloco = t["bloco"]
                marcadores.append((c["ini"], c["secao"].upper(), f"cor dos clipes: {c['cor']}"))
            marcadores += [(c["ini"], "Conferir", x) for x in t["conferir"]]
        if c["ultimo"]:
            marcadores += [(c["fim"] - 1, "TELA: " + x, "") for x in t["tela"]]
    juntos = {}                                            # o Premiere guarda só um marcador por quadro: junta os do mesmo quadro
    for q, nm, cm in marcadores:
        nomes, comentarios = juntos.setdefault(q, ([], []))
        nomes.append(nm)
        comentarios.append(f"{nm}: {cm}" if cm else "")
    mk = "".join(f"<marker><comment>{escape(' | '.join(x for x in cms if x))}</comment><name>{escape(' + '.join(nms))}</name>"
                 f"<in>{q}</in><out>-1</out></marker>" for q, (nms, cms) in sorted(juntos.items()))

    if trilhas_a == 2:
        atr = ['premiereTrackType="Stereo" currentExplodedTrackIndex="0" totalExplodedTrackCount="2"',
               'premiereTrackType="Stereo" currentExplodedTrackIndex="1" totalExplodedTrackCount="2"']
    else:
        atr = ['premiereTrackType="Mono"'] * trilhas_a
    trilhas_audio = "".join(f"<track {atr[j]}>{''.join(a_itens[j])}<enabled>TRUE</enabled><locked>FALSE</locked>"
                            f"<outputchannelindex>{j + 1}</outputchannelindex></track>" for j in range(trilhas_a))
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4">'
           f'<sequence id="sequence-1"><name>{escape(nome_seq)}</name><duration>{pos}</duration>{taxa.xml()}'
           f'<media><video><format><samplecharacteristics>{taxa.xml()}<width>{largura}</width><height>{altura}</height>'
           f'<anamorphic>FALSE</anamorphic><pixelaspectratio>square</pixelaspectratio><fielddominance>none</fielddominance>'
           f'</samplecharacteristics></format><track>{"".join(v_itens)}<enabled>TRUE</enabled><locked>FALSE</locked></track>'
           f'<track><enabled>TRUE</enabled><locked>FALSE</locked></track></video>'
           f'<audio><numOutputChannels>2</numOutputChannels><format><samplecharacteristics><depth>16</depth>'
           f'<samplerate>48000</samplerate></samplecharacteristics></format>{trilhas_audio}</audio></media>'
           f'<timecode>{taxa.xml()}<string>00:00:00:00</string><frame>0</frame><displayformat>NDF</displayformat></timecode>'
           f'{mk}</sequence></xmeml>\n')
    outros = sorted({c["fps"] for c in takes.values() if abs(c["fps"] - taxa.fps) > 0.01})
    resumo = dict(clipes=len(colocados), fim=pos / taxa.fps, crossfades=len(xfs), marcadores=len(juntos),
                  takes=sorted(takes), fps_diferente=outros, trilhas_audio=trilhas_a)
    return xml, resumo, clipes, trechos


# ───── comandos ─────

def _ref(a):
    """fps/tamanho: do XML de referência (--ref), ou de --fps/--largura/--altura."""
    if a.ref:
        sx = ler_xml(a.ref)
        return sx["taxa"], sx["largura"], sx["altura"]
    if not (a.fps and a.largura and a.altura):
        raise ValueError("informe --ref <XML exportado de uma sequência do projeto> ou --fps, --largura e --altura")
    return Taxa.de_fps(a.fps), a.largura, a.altura


def _plano_pedido(proj, caminho):
    if not caminho:
        return None
    return caminho if os.path.exists(caminho) else proj.caminho(caminho)


def cmd_decupar(proj, a):
    taxa, largura, altura = _ref(a)
    arquivo = _plano_pedido(proj, a.plano)
    nome = a.nome or f"{proj.sequencia(a.sequencia)} (decupagem {datetime.datetime.now():%d-%m %Hh%M})"
    xml, r, clipes, trechos = montar_xml(proj, a.sequencia, taxa, largura, altura, nome, arquivo, a.escala)
    print(decupagem.tabela(clipes, trechos))
    saida = os.path.join(proj.pasta_de("transcricoes"), f"decupagem-{proj.chave(a.sequencia)}.premiere.xml")
    if os.path.exists(saida):                              # nunca sobrescreve: o anterior vai para uma subpasta
        bk = os.path.join(proj.pasta_de("transcricoes"), f"_decupagens anteriores ({datetime.datetime.now():%d-%m %Hh%M})")
        os.makedirs(bk, exist_ok=True)
        shutil.move(saida, os.path.join(bk, os.path.basename(saida)))
    open(saida, "w", encoding="utf-8").write(xml)
    print(f"\n✓ XML da decupagem: {saida}")
    print(f"  sequência nova \"{nome}\": {r['clipes']} clipes até {mmss(r['fim'])} · {r['crossfades']} crossfades · "
          f"{r['marcadores']} marcadores · {taxa.fps:.3f} fps {largura}x{altura} · {r['trilhas_audio']} trilha(s) de áudio")
    print("  (o projeto do Premiere não foi alterado; importe com import_fcp_xml, mode into_open_project)")


def cmd_transcrever(proj, a):
    from .transcrever import suspeitas, transcrever       # precisa do faster-whisper
    sx = ler_xml(a.xml)
    wav = proj.arquivo_transcricao(a.sequencia, "wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.wav, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav],
                   check=True)
    for i, f in trechos_mudos(wav):
        print(f"  ⚠ trecho MUDO de {mmss(i)} a {mmss(f)} — confira se o áudio veio na importação")
    mapa = mapa_de_cortes(sx)
    json.dump(mapa, open(proj.arquivo_transcricao(a.sequencia, "cortes.json"), "w", encoding="utf-8"), ensure_ascii=False)
    cfg = proj["transcricao"]
    print(f"transcrevendo '{sx['nome']}' (Whisper)…")
    r = transcrever(wav, proj.arquivo_transcricao(a.sequencia), cfg["modelo"], cfg["idioma"], cfg["nomes"])
    print(f"  {r['palavras']} palavras em {r['segundos']}s ({r['device']})")
    tr = json.load(open(proj.arquivo_transcricao(a.sequencia), encoding="utf-8"))
    for t, w in suspeitas(tr)[:15]:
        print(f"  ⚠ palavra esticada em {mmss(t)}: '{w}' (possível tropeço repetido)")
    achados, faltando, falas = blocos.gerar(proj, a.sequencia, tr, mapa)
    for b in achados if len(achados) > 1 else []:
        print(f"  {mmss(b['t'])}  Bloco {b['n']:>3} · {b['titulo'][:50]}  ({b['nota']:.2f})")
    print(f"documento: {proj.arquivo_transcricao(a.sequencia, 'md')} ({falas} falas)")


def cmd_motions(proj, a):
    taxa, largura, _ = _ref(a)
    cfg = proj["motions"]
    P, fora = motions.planejar(proj, a.sequencia, _plano_pedido(proj, a.plano))
    for p in P:                                            # a tabela do kit, com o timecode no fps desta sequência
        ajuste = f"{p['dur']:.0f}s→{p['len']:.1f}s" if p["encurtado"] else f"{p['dur']:.0f}s"
        print(f"{p['id']:6s} {tc(p['inicio'], taxa.fps)}  {ajuste:11s} {p['nota']:.2f}  {p['nome'][:34]:34s} | {p['ouvido'][:50]}")
    for c, motivo in fora:
        print(f"✗ {c['id']:5s} {'':11s} {'':11s}       {c['nome'][:34]:34s} | {motivo}")
    print(f"{len(P)} motions · encurtados {sum(p['encurtado'] for p in P)} · fora {len(fora)}")
    escala = a.escala if a.escala is not None else round(100 * largura / 1080, 2)     # .mov 1080x1920
    trilha = int(cfg["trilha"].lstrip("Vv")) - 1
    lista = []
    for p in P:
        if p["len"] < cfg["minimo_s"]:
            continue
        pos = round(p["inicio"] * taxa.fps)
        partes = [(0.0, p["len"])] if not p["encurtado"] else [(0.0, p["len"] - cfg["fade_s"]), (p["dur"] - cfg["fade_s"], p["dur"])]
        for k, (de, ate) in enumerate(partes):
            n = max(1, round((ate - de) * taxa.fps))
            lista.append(dict(id=p["id"], parte=k + 1, arquivo=p["arquivo"], nome_item=os.path.basename(p["arquivo"]),
                              inicio_s=round(pos / taxa.fps, 6), entrada_s=round(de, 6),
                              saida_s=round(min(de + n / taxa.fps, p["dur"]), 6),
                              timecode=tc(pos / taxa.fps, taxa.fps)))
            pos += n
    saida = os.path.join(proj.pasta_de("transcricoes"), f"motions-{proj.chave(a.sequencia)}.premiere.json")
    json.dump(dict(sequencia=proj.sequencia(a.sequencia), trilha_video_indice=trilha, escala=escala, fps=taxa.fps,
                   clipes=lista), open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n✓ lista para o Premiere: {saida}")
    print(f"  {len(lista)} clipes na {cfg['trilha']} (índice {trilha}), escala {escala:g} · sem áudio")
    print("  (o projeto do Premiere não foi alterado)")


def cmd_checar(proj, a):
    """Checagens que dá para fazer pelo XML: trilha desligada com clipes, áudio faltando, mídia que não existe no disco.
    Quadro preto (Drive ilegível) e mídia offline no Premiere: o Claude confere com o conector."""
    achados = []
    for arq in a.xml:
        sx = ler_xml(arq)
        nome = sx["nome"]
        for t in sx["video"]:
            if t["itens"] and not t["ligada"]:
                achados.append(("ERRO", nome, f"{t['nome']} tem {len(t['itens'])} clipes mas está desligada"))
        cob_v = sum(c["fim"] - c["inicio"] for c in sx["video"][0]["itens"]) if sx["video"] else 0
        cobs_a = [sum(c["fim"] - c["inicio"] for c in t["itens"]) for t in sx["audio"] if t["itens"]]
        if cobs_a:
            if cob_v and max(cobs_a) < 0.8 * cob_v:
                achados.append(("ERRO", nome, f"áudio cobre {max(cobs_a):.0f}s de {cob_v:.0f}s de vídeo — faltam cortes de áudio"))
        elif cob_v:
            achados.append(("ERRO", nome, "sequência sem nenhum clipe de áudio"))
        sumidos = sorted({os.path.basename(c["caminho"]) for t in sx["video"] + sx["audio"] for c in t["itens"]
                          if c["caminho"] and not os.path.exists(c["caminho"])})
        if sumidos:
            achados.append(("ERRO", nome, f"mídia que não existe no disco: {', '.join(sumidos[:6])}"
                                          + (f" (+{len(sumidos) - 6})" if len(sumidos) > 6 else "")))
    for g, s, m in achados:
        print(f"  {'✗' if g == 'ERRO' else '⚠'} [{s}] {m}")
    print("✓ nenhum problema no XML" if not achados else f"{sum(g == 'ERRO' for g, _, _ in achados)} erro(s)")
    sys.exit(1 if any(g == "ERRO" for g, _, _ in achados) else 0)


def cmd_entregar_xml(proj, a):
    destino = a.destino or proj["drive"]["entrega_xml"] or proj.pasta_de("exports")
    os.makedirs(destino, exist_ok=True)
    backup = os.path.join(destino, f"_XML anteriores ({datetime.datetime.now():%d-%m %Hh%M})")
    for tmp in a.arquivos:
        final = os.path.join(destino, os.path.basename(tmp))
        if os.path.exists(final):
            os.makedirs(backup, exist_ok=True)
            shutil.move(final, os.path.join(backup, os.path.basename(final)))
        shutil.copyfile(tmp, final)
        if os.path.getsize(final) != os.path.getsize(tmp):
            raise IOError(f"cópia incompleta: {final}")
        print("  ✓", final)


def cmd_conferir(proj, a):
    """Transcreve cada clipe planejado SOZINHO (áudio curto) e mostra o que cada um realmente contém.

    O Whisper do take inteiro funde repetições ("Eu gostaria de… Eu gostaria de um prato" vira uma frase só) e às
    vezes perde frases inteiras; transcrito um por um, os falsos começos, as palavras repetidas e os cortes no meio de
    palavra aparecem. Serve para conferir a decupagem antes de importar no Premiere (não muda nada no projeto)."""
    import wave
    import numpy as np
    from .transcrever import _carregar
    clipes, _, erros = decupagem.planejar(proj, a.sequencia, a.plano, a.fps)
    if erros:
        raise ValueError("a decupagem tem erros (rode 'decupar' para ver): " + "; ".join(erros))
    pasta = decupagem.pasta_brutos(proj)
    modelo, _ = _carregar(proj["transcricao"]["modelo"])
    audios, saida, avisos_total = {}, [], 0
    prompt = "Eh... eu gostaria de... eu gostaria de um prato. É, é isso, é isso que eu quero."

    def texto_de(c):
        if c["take"] not in audios:
            with wave.open(os.path.join(pasta, c["take"] + ".wav"), "rb") as w:
                audios[c["take"]] = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
        x = audios[c["take"]]
        a0, b0 = max(0.0, c["a"] - 0.25), c["b"] + 0.4
        segs, _ = modelo.transcribe(x[int(a0 * 16000):int(b0 * 16000)], language="pt", word_timestamps=False, vad_filter=False,
                                    condition_on_previous_text=False, initial_prompt=prompt, beam_size=5, temperature=0)
        return " ".join(s.text.strip() for s in segs).strip()

    palavras = lambda t: re.findall(r"\w+", t.lower())
    textos = [texto_de(c) for c in clipes]
    for i, c in enumerate(clipes):
        ps, flags = palavras(textos[i]), []
        dur = c["b"] - c["a"]
        if len(ps) <= 3 and dur < 1.5:
            flags.append("fragmento curto: tropeço ou conversa de set?")
        if i + 1 < len(clipes) and clipes[i + 1]["take"] == c["take"]:
            pn = palavras(textos[i + 1])
            if len(ps) >= 2 and len(pn) >= 2 and (ps[-2:] == pn[:2] or ps[:min(3, len(ps))] == pn[:min(3, len(ps))]):
                flags.append("repete o começo do próximo clipe: falso começo?")
        saida.append(f"{i:3d}  {c['take']} {mmss(c['a'])}-{mmss(c['b'])}  {textos[i]}" + "".join(f"\n       ⚠ {f}" for f in flags))
        avisos_total += len(flags)
    texto = "\n".join(saida)
    arq = os.path.join(proj.pasta_de("transcricoes"), f"conferencia-{proj.chave(a.sequencia)}.md")
    open(arq, "w", encoding="utf-8").write(f"# Conferência clipe a clipe — {a.sequencia}\n\nCada linha é um clipe transcrito sozinho. "
                                           f"Procure falsos começos, palavras repetidas e frases que terminam cortadas.\n\n```\n{texto}\n```\n")
    print(texto)
    print(f"\n{len(clipes)} clipes conferidos · {avisos_total} avisos · {arq}")


def main(argv=None):
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="premiere.cmd", description="Kit STLFLIX com o Premiere Pro (versão local)")
    ap.add_argument("--projeto", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def ref(p):
        p.add_argument("--ref", help="XML (FCP7) exportado de uma sequência do projeto: dá o fps e o tamanho")
        p.add_argument("--fps", type=float)
        p.add_argument("--largura", type=int)
        p.add_argument("--altura", type=int)

    p = sub.add_parser("decupar", help="decupagem aprovada → XML de uma sequência nova para importar no Premiere")
    p.add_argument("sequencia")
    p.add_argument("--plano", help="outro arquivo de decupagem")
    p.add_argument("--nome", help="nome da sequência nova (padrão: '<sequência> (decupagem dd-mm HHhMM)')")
    p.add_argument("--escala", type=float, help="escala do Movimento nos takes (ex.: 50 para bruto 4K numa sequência 1080x1920)")
    ref(p)
    p = sub.add_parser("conferir", help="transcreve cada clipe da decupagem sozinho: acha falsos começos, repetições e cortes no meio da palavra")
    p.add_argument("sequencia")
    p.add_argument("--plano", help="outro arquivo de decupagem")
    p.add_argument("--fps", type=float, default=29.97, help="fps da sequência (padrão 29,97)")
    p = sub.add_parser("transcrever", help="transcreve uma sequência a partir do XML e do WAV exportados pelo Premiere")
    p.add_argument("sequencia")
    p.add_argument("--xml", required=True)
    p.add_argument("--wav", required=True)
    p = sub.add_parser("motions", help="encaixe dos motions → lista JSON para o Claude colocar no Premiere")
    p.add_argument("sequencia")
    p.add_argument("--plano")
    p.add_argument("--escala", type=float, help="escala dos .mov (padrão: largura da sequência / 1080 × 100)")
    ref(p)
    p = sub.add_parser("checar", help="checagens pelo XML exportado (trilhas, áudio, mídia sumida)")
    p.add_argument("--xml", action="append", required=True)
    p = sub.add_parser("entregar-xml", help="copia XMLs exportados para a entrega, guardando os anteriores")
    p.add_argument("arquivos", nargs="+")
    p.add_argument("--destino")
    a = ap.parse_args(argv)
    try:
        proj = Projeto(vsls.resolver(a.projeto))
        globals()["cmd_" + a.cmd.replace("-", "_")](proj, a)
    except (FileNotFoundError, FileExistsError, KeyError, ValueError) as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

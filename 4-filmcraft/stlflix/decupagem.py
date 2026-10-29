"""Decupagem com o Claude: transcrição dos brutos → decupagem aprovada pelo editor → sequência montada no FilmCraft.

1. transcrever_brutos: cada take da câmera vira 06-transcricoes/brutos/<take>.json (+ .wav 16 kHz), e
   escrever_brutos_md junta tudo em 06-transcricoes/brutos.md, com o tempo de cada frase no bruto e os possíveis tropeços.
2. O Claude cruza esse documento com a copy e escreve 06-transcricoes/decupagem-<seq>.md; o editor aprova.
3. planejar/aplicar: cada trecho "usa" vira clipes no estilo medido nas montagens (5-guias/estilo-de-edicao.md):
   cabeça 2 quadros antes da fala e cauda 5,5 depois (pela energia do áudio, não pelo Whisper), pausas de 0,3 s ou
   mais cortadas, crossfade Constant Power de 3 quadros no meio da frase e 10 no fim. Veio do
   _legado/vsl-hugo/montar_corpo2.py, que montou a VSL do Hugo.

Formato da decupagem (uma linha por trecho do bruto; a ordem dos "usa" é a ordem na timeline):

    ## Bloco 05 · Luan
    - C2347 00:11.3-00:23.0 · usa · Expositor + lojas de lembrancinhas
    - C2347 00:25.0-00:35.9 · usa · Petare (parte 1) — falou "participou do reality" (copy: "do reality show")
      conferir: ouvir se ele disse "margem"          ← marcador no começo do trecho, na timeline
      tela: Cotrim entregando os ímãs                 ← marcador no fim do trecho (ideia de B-roll)
    - C2347 00:35.9-00:41.2 · descarta · "Em que a gente visita…" (2 tentativas)
    - C2347 00:06.1-00:11.3 · alternativa · versão completa da frase
"""
import json
import os
import re
import subprocess
import wave

import numpy as np

from .tempo import T, fps, frame_ticks, mmss
from .texto import aplicar_grafias

CABECA_Q, CAUDA_Q, PAUSA_MIN = 2.0, 5.5, 0.30        # quadros antes/depois da fala; pausa interna que sai
XF_MEIO, XF_FIM = 3, 10                               # crossfade (quadros) no meio da frase / em fim de frase
FPS_PADRAO = 24000 / 1001                             # só para a prévia; na montagem vale o da sequência
CORES = {"usa": "Green", "alternativa": "Yellow", "descarta": "Rose", "nota": "Blue"}
VIDEO = (".mov", ".mp4", ".mxf", ".mts", ".m4v", ".avi")

LINHA = re.compile(r"^\s*[-*]\s*([\w.\-]+)\s+(\d[\d:.,]*)\s*[-–]\s*(\d[\d:.,]*)\s*·\s*(usa|alternativa|descarta|nota)\s*(?:·\s*(.*))?$", re.I)
TITULO = re.compile(r"^#{2,3}\s+(.+?)\s*$")
EXTRA = re.compile(r"^\s+(conferir|tela)\s*:\s*(.+)$", re.I)


def pasta_brutos(proj):
    p = os.path.join(proj.pasta_de("transcricoes"), "brutos")
    os.makedirs(p, exist_ok=True)
    return p


def arquivo_decupagem(proj, chave):
    return os.path.join(proj.pasta_de("transcricoes"), f"decupagem-{proj.chave(chave)}.md")


# ───── 1. transcrição dos brutos ─────

def takes_do_projeto(fc, prefixo):
    """{take: {path, item}} dos vídeos importados no FilmCraft cujo nome começa com o prefixo da câmera."""
    out = {}
    for m in fc.run("media.status"):
        nome, ext = os.path.splitext(m.get("name") or "")
        if ext.lower() in VIDEO and nome.upper().startswith(prefixo.upper()) and m.get("path"):
            out[nome] = dict(path=m["path"], item=m["item"])
    return out


def takes_da_pasta(pasta, prefixo):
    out = {}
    for raiz, _, nomes in os.walk(pasta):
        for n in nomes:
            nome, ext = os.path.splitext(n)
            if ext.lower() in VIDEO and nome.upper().startswith(prefixo.upper()):
                out.setdefault(nome, dict(path=os.path.join(raiz, n), item=None))
    return out


def transcrever_brutos(proj, takes, so=None, refazer=False):
    """Gera (take, resultado) a cada take; resultado None = já estava transcrito (e o bruto não mudou)."""
    from .transcrever import transcrever           # só aqui: precisa do faster-whisper
    pasta, cfg = pasta_brutos(proj), proj["transcricao"]
    indice = os.path.join(pasta, "takes.json")
    try:
        conhecidos = json.load(open(indice, encoding="utf-8"))
    except (OSError, ValueError):
        conhecidos = {}
    conhecidos.update(takes)
    json.dump(conhecidos, open(indice, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for take in sorted(takes):
        if so and take not in so:
            continue
        js, wav = os.path.join(pasta, take + ".json"), os.path.join(pasta, take + ".wav")
        fonte = takes[take]["path"]
        if not refazer and os.path.exists(js) and os.path.exists(wav) and os.path.getmtime(js) >= os.path.getmtime(fonte):
            yield take, None
            continue
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", fonte, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav],
                       check=True)
        yield take, transcrever(wav, js, cfg["modelo"], cfg["idioma"], cfg["nomes"])


def escrever_brutos_md(proj, max_palavra_s=0.8, pausa_s=2.0):
    """06-transcricoes/brutos.md: cada take com as frases no tempo do bruto, pausas longas e palavras esticadas
    (o Whisper funde tropeços repetidos numa palavra longa: fique com a última repetição limpa)."""
    pasta = pasta_brutos(proj)
    grafias = proj["transcricao"].get("grafias")
    takes = sorted(n[:-5] for n in os.listdir(pasta) if n.endswith(".json") and n != "takes.json")
    linhas = [f"# Transcrição dos brutos — {proj['nome'] or os.path.basename(proj.pasta)}", "",
              "Tempos = posição no bruto (mm:ss.d). ⚠ = palavra esticada (possível tropeço repetido). "
              "Use para escrever a decupagem: `decupagem-<seq>.md`.", ""]
    for take in takes:
        tr = json.load(open(os.path.join(pasta, take + ".json"), encoding="utf-8"))
        linhas += [f"## {take}  ·  {mmss(tr.get('duration') or 0)} de bruto", ""]
        fim_ant = 0.0
        for s in tr["segments"]:
            if s["start"] - fim_ant >= pausa_s:
                linhas.append(f"- _(pausa de {s['start'] - fim_ant:.1f} s)_")
            esticadas = [w["text"] for w in tr["words"] if s["start"] - 0.05 <= w["start"] < s["end"] and w["end"] - w["start"] > max_palavra_s]
            alerta = f"  ⚠ esticada: {', '.join(esticadas)}" if esticadas else ""
            linhas.append(f"- **{mmss(s['start'])}–{mmss(s['end'])}** {aplicar_grafias(s['text'].strip(), grafias)}{alerta}")
            fim_ant = s["end"]
        linhas.append("")
    caminho = os.path.join(proj.pasta_de("transcricoes"), "brutos.md")
    open(caminho, "w", encoding="utf-8").write("\n".join(linhas))
    return caminho, takes


# ───── 2. ler a decupagem ─────

def _segundos(txt):
    s = 0.0
    for p in txt.replace(",", ".").split(":"):
        s = s * 60 + float(p)
    return s


def ler(caminho):
    """[{take, a, b, tipo, rotulo, comentario, bloco, conferir, tela, linha}] na ordem do arquivo, e os erros de escrita."""
    trechos, erros, bloco = [], [], ""
    for k, linha in enumerate(open(caminho, encoding="utf-8"), 1):
        m = TITULO.match(linha)
        if m:
            bloco = m.group(1)
            continue
        m = LINHA.match(linha)
        if m:
            take, a, b, tipo, resto = m.groups()
            rotulo, _, comentario = (resto or "").partition(" — ")
            t = dict(take=take, a=_segundos(a), b=_segundos(b), tipo=tipo.lower(), rotulo=rotulo.strip() or take,
                     comentario=comentario.strip(), bloco=bloco, conferir=[], tela=[], linha=k)
            if t["b"] <= t["a"]:
                erros.append(f"linha {k}: o fim ({b}) vem antes do começo ({a})")
            trechos.append(t)
            continue
        m = EXTRA.match(linha)
        if m and trechos:
            trechos[-1][m.group(1).lower()].append(m.group(2).strip())
    usados = [t for t in trechos if t["tipo"] == "usa"]
    for i, t in enumerate(usados):
        for u in usados[i + 1:]:
            if u["take"] == t["take"] and u["a"] < t["b"] and t["a"] < u["b"]:
                erros.append(f"linha {u['linha']}: o trecho {mmss(u['a'])}-{mmss(u['b'])} do {u['take']} repete parte do da linha {t['linha']}")
    return trechos, erros


# ───── 3. cortes pela energia do áudio ─────

def energia(wav):
    """(fala, dB) em janelas de 10 ms: fala = 18 dB acima do ruído de fundo do take."""
    with wave.open(wav, "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    hop = 160
    n = len(x) // hop
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    db = 20 * np.log10(rms + 1e-9)
    return db > np.percentile(db, 10) + 18, db


def _mais_baixo(db, t, antes=0.35, depois=0.05):
    i0, i1 = max(0, int(round((t - antes) * 100))), int(round((t + depois) * 100))
    return (i0 + int(np.argmin(db[i0:i1]))) / 100 if i1 > i0 else t


def refinar(md, a, b, quadro_fps):
    """Divide [a, b] do bruto em clipes em volta da fala; devolve (clipes, avisos)."""
    fala, db = md
    avisos = []
    if fala[int(round(a * 100)):int(round(a * 100)) + 3].any():
        a = _mais_baixo(db, a, antes=0.05, depois=0.35)
        avisos.append(f"o começo caía no meio da fala: cortado no ponto mais baixo ({mmss(a)})")
    if fala[max(0, int(round(b * 100)) - 3):int(round(b * 100))].any():
        b = _mais_baixo(db, b)
        avisos.append(f"o fim caía no meio da fala: cortado no ponto mais baixo ({mmss(b)})")
    i0, i1 = int(round(a * 100)), int(round(b * 100))
    idx = np.flatnonzero(fala[i0:i1])
    if idx.size == 0:
        return [], ["sem fala no trecho"]
    ilhas, s, ant = [], idx[0], idx[0]
    for k in idx[1:]:
        if (k - ant) / 100 >= 0.10:
            ilhas.append((s, ant + 1))
            s = k
        ant = k
    ilhas.append((s, ant + 1))
    ilhas = [(i0 + x, i0 + y) for x, y in ilhas if y - x >= 6]          # cliques de menos de 60 ms não contam
    clipes = []
    for on, off in ilhas:
        ini = max(a, on / 100 - CABECA_Q / quadro_fps)
        fim = min(b, off / 100 + CAUDA_Q / quadro_fps)
        if clipes and ini - clipes[-1][1] < PAUSA_MIN:                   # só sai pausa de 0,3 s ou mais
            clipes[-1] = (clipes[-1][0], fim)
        else:
            clipes.append((ini, fim))
    return clipes, avisos


def _fim_de_frase(palavras, t, fim_do_trecho=False):
    """O corte em t fecha uma frase? No fim de um trecho, t é o fim escrito na decupagem e vale a última palavra com
    o meio antes dele: o corte pela energia cai antes do fim que o Whisper marca, e a última palavra ficaria de fora."""
    antes = [w for w in palavras if ((w["start"] + w["end"]) / 2 < t if fim_do_trecho else w["end"] <= t + 0.05)]
    depois = [w for w in palavras if w["start"] >= t - 0.05 and w not in antes]
    p = antes[-1]["text"] if antes else ""
    n = depois[0]["text"] if depois else ""
    vao = (depois[0]["start"] - antes[-1]["end"]) if antes and depois else 0
    return p.endswith((".", "?", "!")) or (n[:1].isupper() and not p.endswith(",") and vao >= 0.5)


def planejar(proj, chave, arquivo=None, quadro_fps=FPS_PADRAO):
    """Clipes na ordem da timeline: [{take, a, b, primeiro, ultimo, trecho, avisos, xf}], trechos e erros."""
    arquivo = arquivo or arquivo_decupagem(proj, chave)
    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"ainda não existe a decupagem: {arquivo}")
    trechos, erros = ler(arquivo)
    pasta, cache, clipes = pasta_brutos(proj), {}, []
    for t in (t for t in trechos if t["tipo"] == "usa"):
        if t["take"] not in cache:
            wav, js = os.path.join(pasta, t["take"] + ".wav"), os.path.join(pasta, t["take"] + ".json")
            if not (os.path.exists(wav) and os.path.exists(js)):
                erros.append(f"linha {t['linha']}: o {t['take']} não foi transcrito (rode transcrever-brutos)")
                cache[t["take"]] = None
                continue
            cache[t["take"]] = (energia(wav), json.load(open(js, encoding="utf-8"))["words"])
        if cache[t["take"]] is None:
            continue
        md, palavras = cache[t["take"]]
        partes, avisos = refinar(md, t["a"], t["b"], quadro_fps)
        if not partes:
            erros.append(f"linha {t['linha']}: {t['take']} {mmss(t['a'])}-{mmss(t['b'])} não tem fala")
        for k, (a, b) in enumerate(partes):
            clipes.append(dict(take=t["take"], a=a, b=b, primeiro=k == 0, ultimo=k == len(partes) - 1, trecho=t,
                               avisos=avisos if k == 0 else [], palavras=palavras))
    for i, c in enumerate(clipes):
        prox = clipes[i + 1] if i + 1 < len(clipes) else None
        if prox is None:
            c["xf"] = None
        elif prox["take"] != c["take"] or prox["primeiro"]:
            c["xf"] = XF_FIM if _fim_de_frase(c["palavras"], c["trecho"]["b"], fim_do_trecho=True) else XF_MEIO
        else:
            c["xf"] = XF_FIM if _fim_de_frase(c["palavras"], (c["b"] + prox["a"]) / 2) else XF_MEIO
    return clipes, trechos, erros


def tabela(clipes, trechos):
    linhas, bloco = [], None
    for c in clipes:
        t = c["trecho"]
        if t["bloco"] != bloco:
            bloco = t["bloco"]
            linhas.append(f"\n{bloco or '(sem bloco)'}")
        if c["primeiro"]:
            n = sum(1 for x in clipes if x["trecho"] is t)
            linhas.append(f"  {t['take']:8s} {mmss(t['a'])}-{mmss(t['b'])}  {n} clipe{'s' if n > 1 else ''}  {t['rotulo'][:60]}"
                          + "".join(f"\n      ⚠ {x}" for x in c["avisos"])
                          + "".join(f"\n      conferir: {x}" for x in t["conferir"]))
    total = sum(c["b"] - c["a"] for c in clipes)
    fora = [t for t in trechos if t["tipo"] in ("descarta", "alternativa")]
    linhas.append(f"\n{len(clipes)} clipes, {total / 60:.1f} min de fala · crossfades: {sum(c['xf'] == XF_MEIO for c in clipes)} de "
                  f"{XF_MEIO} quadros, {sum(c['xf'] == XF_FIM for c in clipes)} de {XF_FIM} · {len(fora)} trechos descartados ou alternativos")
    return "\n".join(linhas)


# ───── 4. montar no FilmCraft ─────

def aplicar(fc, proj, chave, arquivo=None):
    """Faz backup da sequência, tira dela os brutos usados e monta a decupagem a partir do fim da V1 que sobrar."""
    nome = proj.sequencia(chave)
    seqs = fc.sequencias()
    if nome not in seqs:
        raise KeyError(f"a sequência '{nome}' não existe no projeto: crie uma sequência com esse nome (pode ser vazia)")
    sid = seqs[nome]
    fc.run("sequence.open", item=sid)
    seq = fc.run("sequence.inspect", item=sid)
    f, FR = fps(seq), frame_ticks(seq)
    clipes, trechos, erros = planejar(proj, chave, arquivo, f)
    if erros:
        raise ValueError("a decupagem tem erros: " + "; ".join(erros[:5]))

    # o item de cada take no projeto (importa o que faltar, pelo caminho anotado na transcrição dos brutos)
    usados = {t["take"] for t in trechos}
    itens = {os.path.splitext(m["name"])[0]: m["item"] for m in fc.run("media.status")
             if os.path.splitext(m.get("name") or "")[0] in usados}
    faltam = usados - set(itens)
    if faltam:
        conhecidos = json.load(open(os.path.join(pasta_brutos(proj), "takes.json"), encoding="utf-8"))
        caminhos = [conhecidos[t]["path"] for t in faltam if t in conhecidos]
        if caminhos:
            fc.run("file.import", paths=caminhos)
        itens.update({os.path.splitext(m["name"])[0]: m["item"] for m in fc.run("media.status")
                      if os.path.splitext(m.get("name") or "")[0] in faltam})
        if usados - set(itens):
            raise KeyError(f"takes que não estão no projeto: {', '.join(sorted(usados - set(itens)))}")

    fc.run("project.select", items=[sid])                    # backup antes de tirar os brutos da sequência
    fc.run("edit.duplicate")
    brutos = [c["clip"] for t in seq["video"] + seq["audio"] for c in t["items"] if c["item"] in set(itens.values())]
    if brutos:
        fc.run("edit.clear", clips=brutos)
    seq = fc.run("sequence.inspect", item=sid)
    pos = round(max((c["end"] for c in seq["video"][0]["items"]), default=0) / FR) if seq["video"] else 0
    inicio = pos

    pasta = pasta_brutos(proj)                               # transcrição e marcadores no bruto, para conferir no visualizador
    for take, item in itens.items():
        palavras = json.load(open(os.path.join(pasta, take + ".json"), encoding="utf-8"))["words"]
        fc.run("transcript.set", item=item, transcript={"language": proj["transcricao"]["idioma"], "speakers": [{"name": "Apresentador"}],
               "words": [{"text": w["text"], "start": round(w["start"] * T), "end": round(max(w["end"], w["start"]) * T), "speaker": 0}
                         for w in palavras if w["text"]]})
        fc.run("source.open", item=item)
        for t in (t for t in trechos if t["take"] == take):
            fc.run("markers.add", target="source", time=round(t["a"] * T), durationFrames=max(1, round((t["b"] - t["a"]) * f)),
                   name=t["rotulo"], comment=t["comentario"], color=CORES[t["tipo"]])

    colocados, marcadores, bloco = [], [], None
    for c in clipes:
        q_in, q_out = round(c["a"] * f), round(c["b"] * f)
        n = q_out - q_in
        r = fc.run("timeline.place", item=itens[c["take"]], track="V1", audioTrack="A1", time=pos * FR,
                   sourceIn=q_in * FR, duration=n * FR, insert=False)
        colocados += r["clips"]
        t = c["trecho"]
        if c["primeiro"]:
            if t["bloco"] and t["bloco"] != bloco:
                bloco = t["bloco"]
                marcadores.append(dict(time=pos * FR, name=bloco.upper(), color="Blue", comment=""))
            marcadores += [dict(time=pos * FR, name="Conferir", color="Mango", comment=x) for x in t["conferir"]]
        if c["ultimo"]:
            marcadores += [dict(time=(pos + n - 1) * FR, name="TELA: " + x, color="Lavender", comment="") for x in t["tela"]]
        pos += n
    for m in marcadores:
        fc.run("markers.add", target="program", **m)

    seq = fc.run("sequence.inspect", item=sid)               # crossfades nos cortes encostados da A1 nova
    a1 = sorted((c for c in seq["audio"][0]["items"] if c["clip"] in set(colocados)), key=lambda c: c["start"]) if seq["audio"] else []
    feitos = 0
    for k, (c, prox) in enumerate(zip(a1, a1[1:])):
        xf = clipes[k]["xf"] if k < len(clipes) else None
        if xf and c["endFrame"] == prox["startFrame"]:
            fc.run("sequence.applyAudioTransition", clip=c["clip"], edge="out", effect="constant_power", frames=xf)
            feitos += 1
    return dict(clipes=len(clipes), inicio=inicio * FR / T, fim=pos * FR / T, crossfades=feitos, marcadores=len(marcadores),
                tirados=len(brutos))

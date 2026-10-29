"""Encaixe dos motions (.mov transparentes do HyperFrames) na timeline, cada um na sua frase-gatilho.

Regras (as mesmas usadas nas VSLs do Hugo e do Shark):
- o motion entra `antecedencia_s` (0,2 s) antes da primeira palavra da frase-gatilho, na trilha de motions
  (V2) em escala 200 (o .mov é 1080x1920 numa sequência 2160x3840);
- se ele encostaria no próximo, é encurtado: fica o começo e emendam-se os últimos `fade_s` (0,5 s) do .mov;
  o último termina com a sequência;
- cena cuja frase não aparece na fala (versão curta, trecho cortado) fica de fora e é listada.
"""
import json
import os
import subprocess

from . import plano as plano_mod
from .tempo import T, frame_ticks, fps, tc
from .texto import achar, tokens_da_transcricao

NOTA_MIN = 0.75


def duracao(arquivo):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", arquivo],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def arquivos_motion(pasta):
    """{código: caminho} dos .mov da pasta (e subpastas): B05A-nome.mov → B05A.
    Pastas que começam com "_" são backup ("_motions anteriores …") e ficam de fora."""
    out = {}
    for raiz, pastas, nomes in os.walk(pasta):
        pastas[:] = [p for p in pastas if not p.startswith("_")]
        for n in nomes:
            if n.lower().endswith(".mov"):
                out.setdefault(n.split("-")[0].split(".")[0], os.path.join(raiz, n))
    return out


def planejar(proj, chave, caminho_plano=None, exigir_mov=True):
    """Onde cada motion entra. exigir_mov=False só confere as frases-gatilho (serve para rascunho, antes do render)."""
    cfg = proj["motions"]
    tr = json.load(open(proj.arquivo_transcricao(chave), encoding="utf-8"))
    sin = proj["transcricao"].get("sinonimos")
    tokens = tokens_da_transcricao(tr, sin)
    total = tr.get("duration") or (tr["words"][-1]["end"] if tr["words"] else 0)
    try:
        blocos = {a["n"]: a["t"] for a in json.load(open(proj.arquivo_transcricao(chave, "blocos.json"), encoding="utf-8"))["achados"]}
    except FileNotFoundError:
        blocos = {}
    cenas = plano_mod.ler(caminho_plano or proj.plano(chave))
    movs = arquivos_motion(proj.pasta_de("motions"))
    ordem_blocos = sorted(blocos.values())
    P, fora, cursor = [], [], 0
    for c in cenas:
        if c["bloco"] and blocos and c["bloco"] not in blocos:
            fora.append((c, "bloco fora desta sequência"))
            continue
        ini, fim = cursor, None
        if c["bloco"] in blocos:                   # procura dentro do bloco
            a = blocos[c["bloco"]]
            prox = [t for t in ordem_blocos if t > a]
            ini = max(cursor, next((i for i, (_, t) in enumerate(tokens) if t >= a - 0.5), 0))
            fim = next((i for i, (_, t) in enumerate(tokens) if prox and t >= prox[0] + 0.5), None)
        i, nota = achar(tokens, c["gatilho"], ini, fim, sin)
        if i is None or nota < NOTA_MIN:           # fora de ordem? tenta no vídeo todo
            i2, n2 = achar(tokens, c["gatilho"], 0, None, sin)
            if i2 is not None and n2 >= max(nota, NOTA_MIN):
                i, nota = i2, n2
        if i is None or nota < NOTA_MIN:
            fora.append((c, f"frase não encontrada (melhor {nota:.2f})"))
            continue
        if exigir_mov and c["id"] not in movs:
            fora.append((c, "falta o .mov na pasta de motions"))
            continue
        cursor = i + 1
        dur = duracao(movs[c["id"]]) if c["id"] in movs else 0.0
        P.append(dict(id=c["id"], nome=c["nome"], arquivo=movs.get(c["id"]), dur=dur, nota=round(nota, 2),
                      inicio=max(0.0, tokens[i][1] - cfg["antecedencia_s"]),
                      ouvido=" ".join(t for t, _ in tokens[i:i + 8])))
    P.sort(key=lambda p: p["inicio"])
    for k, p in enumerate(P):
        espaco = (P[k + 1]["inicio"] - cfg["folga_s"] - p["inicio"]) if k + 1 < len(P) else (total - p["inicio"])
        p["len"] = min(p["dur"], espaco)
        p["encurtado"] = p["len"] < p["dur"] - 1e-6
    return P, fora


def aplicar(fc, proj, chave, P):
    cfg = proj["motions"]
    nome_seq = proj.sequencia(chave)
    seq_id = fc.sequencias()[nome_seq]
    tem = fc.itens_mov()
    faltam = [p["arquivo"] for p in P if os.path.basename(p["arquivo"]) not in tem]
    if faltam:
        fc.run("file.import", paths=faltam)
        tem = fc.itens_mov()
    fc.run("sequence.open", item=seq_id)
    seq = fc.run("sequence.inspect", item=seq_id)
    FR = frame_ticks(seq)
    trilha_nome = "Video " + cfg["trilha"].lstrip("Vv")
    trilha = next((t for t in seq["video"] if t["name"] == trilha_nome), None)
    if trilha:
        antigos = [c["clip"] for c in trilha["items"] if c["name"].lower().endswith(".mov")]
        if antigos:
            fc.run("edit.clear", clips=antigos)
    colocados = []
    for p in P:
        if p["len"] < cfg["minimo_s"]:
            continue
        pos = round(p["inicio"] * fps(seq))
        partes = [(0.0, p["len"])] if not p["encurtado"] else [(0.0, p["len"] - cfg["fade_s"]), (p["dur"] - cfg["fade_s"], p["dur"])]
        for a, b in partes:
            n = max(1, round((b - a) * fps(seq)))
            r = fc.run("timeline.place", item=tem[os.path.basename(p["arquivo"])], track=cfg["trilha"], time=pos * FR,
                       sourceIn=round(a * T), duration=n * FR, insert=False, audio=False)
            colocados += r["clips"]
            pos += n
    seq = fc.run("sequence.inspect", item=seq_id)
    for c in (c for t in seq["video"] for c in t["items"] if c["clip"] in colocados):
        mi = [e["effect"] for e in c["effects"]].index("motion")
        fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=cfg["escala"])
    trilha = next(t for t in seq["video"] if t["name"] == trilha_nome)
    if not trilha["enabled"]:                      # sequências vindas de XML chegam com a V2 desligada
        fc.run("timeline.setTrack", track=trilha["id"], enabled=True)
    return len(colocados)


def tabela(P, fora):
    linhas = []
    for p in P:
        ajuste = f"{p['dur']:.0f}s→{p['len']:.1f}s" if p["encurtado"] else f"{p['dur']:.0f}s"
        linhas.append(f"{p['id']:6s} {tc(p['inicio'])}  {ajuste:11s} {p['nota']:.2f}  {p['nome'][:34]:34s} | {p['ouvido'][:50]}")
    for c, motivo in fora:
        linhas.append(f"✗ {c['id']:5s} {'':11s} {'':11s}       {c['nome'][:34]:34s} | {motivo}")
    linhas.append(f"{len(P)} motions · encurtados {sum(p['encurtado'] for p in P)} · fora {len(fora)}")
    return "\n".join(linhas)

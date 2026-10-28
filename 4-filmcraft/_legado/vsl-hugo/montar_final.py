"""C2351 (new ending, 12x de R$ 490): replace the C2349 ending after '…nem muito menos sessenta mil reais.'
Reuses refine()/is_boundary() from montar_corpo2 (energy-based handles, pause removal, crossfade rule).

Usage: python montar_final.py plan | apply
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import montar_corpo2 as m
from fc import FC

T, FPS, FRAME = m.T, m.FPS, m.FRAME
USE, ALT, DROP, NOTE = m.USE, m.ALT, m.DROP, m.NOTE
ITEM, RAW = 1, [885, 887]                       # C2351 raw clips on V1/A1
KEEP_LAST_2349 = 766                             # '…nem muito menos sessenta mil reais.' stays
REMOVE_2349 = [769, 772, 775, 778, 781, 784]     # old 497 / referência / cupons (video ids)
OLD_MARKERS = ("Conferir: PARCELA", "TELA: 'R$ 4.997", "FALTA: explicação dos cupons")

BLOCKS = [
    (0.0, 2.72, DROP, "Fragmento 'Você leva tudo isso pra sempre'", "", []),
    (6.86, 10.24, NOTE, "'Vou fazer um pouquinho antes'", "", []),
    (10.8, 16.55, ALT, "'Mas nessa Black… 9.015, nem menos 60 mil'",
     "Tropeço nos valores; a montagem usa essa frase do C2349 ('nove mil, quinze mil, nem muito menos sessenta mil').", []),
    (16.58, 26.9, USE, "Investimento: R$ 4.997 ou 12x de R$ 490", "", [
        ("end", "TELA: 'R$ 4.997 à vista ou 12x de R$ 490'", "Lavender", "")]),
    (27.72, 28.46, NOTE, "'Valendo, né?'", "", []),
    (37.6, 69.2, USE, "Referência + cupons: 334 de R$ 15, válidos por 2 anos",
     "Ad-lib 'como eu já disse antes'. Disse 'que você recebe na hora' (copy: 'liberados ao longo de 12 meses').", [
        ("end", "Conferir: cupons 'recebe na hora'?", "Mango",
         "Hugo improvisou '334 cupons de R$ 15 que você recebe na hora e que são válidos por dois anos'. "
         "A copy (e o take antigo) diz 'liberados ao longo de 12 meses, [X] por mês'. Confirmar a regra com o cliente.")]),
    (72.12, 114.14, DROP, "Comemoração / conversa", "", []),
    (117.2, 129.5, USE, "Somando todos → o acesso vitalício vai junto", "", [
        ("end", "TELA: 'R$ 4.997 de volta em cupons de filamento'", "Lavender", "")]),
    (131.06, 134.78, NOTE, "'Estamos chegando ao fim: escassez agora'", "", []),
    (140.3, 147.8, USE, "Escassez: os cupons são limitados", "", [("start", "ESCASSEZ E FECHAMENTO", "Blue", "")]),
    (148.0, 164.52, DROP, "'Isso porque cada vaga…' take 1 + 'ficou bom isso, mas eu…'", "", []),
    (165.6, 192.3, USE, "Compromisso de filamento → oferta sai do ar",
     "Ad-libs: 'a gente aumentou o nosso estoque… agora comporta todo mundo', 'a gente não tem como garantir'.", []),
    (192.44, 205.14, DROP, "Recapitulação take 1 ('estava tão bom')", "", []),
    (205.9, 234.2, USE, "Recapitulação + CTA", "", [("end", "CTA: QUERO O VITALÍCIO", "Lavender", "Botão aparecendo na tela.")]),
    (235.5, 240.9, USE, "Despedida: te encontro do outro lado", "Copy: 'Eu quero ver você vendendo. A gente se encontra lá dentro.'", [
        ("end", "Recado do Hugo: 'Põe o efeito da lâmina'", "Mango", "No fim da gravação: 'Põe o efeito da lâmina, editor.'")]),
    (243.90, 246.30, NOTE, "Recado: 'Põe o efeito da lâmina, editor'", "", []),
    (247.84, 250.08, DROP, "Comemoração", "", []),
]


def plan():
    md, words = m.load("C2351")
    out = []
    for a, b, color, label, _, marks in BLOCKS:
        if color != USE:
            continue
        clips, warn = m.refine(md, a, b)
        for k, (s, e) in enumerate(clips):
            mk = [x for x in marks if (x[0] == "start" and k == 0) or (x[0] == "end" and k == len(clips) - 1)]
            out.append({"in": s, "out": e, "take": label, "first": k == 0, "markers": mk, "warn": warn if k == 0 else []})
    for i, c in enumerate(out):
        nx = out[i + 1] if i + 1 < len(out) else None
        if nx is None:
            c["xf"] = None
        elif nx["first"]:  # cut between two different takes: boundary unless the sentence goes on after a comma
            last = [w["text"] for w in words if w["end"] <= c["out"] + 0.05]
            c["xf"] = m.XF_MID if last and last[-1].endswith(",") else m.XF_BOUNDARY
        else:
            c["xf"] = m.XF_BOUNDARY if m.is_boundary(words, (c["out"] + nx["in"]) / 2) else m.XF_MID
    return out, words


if __name__ == "__main__":
    P, words = plan()
    if sys.argv[1] == "plan":
        for c in P:
            if c["first"]:
                print(c["take"] + (f"   ⚠ {', '.join(c['warn'])}" if c["warn"] else ""))
            print(f"    {m.fmt(c['in'])}-{m.fmt(c['out'])} ({c['out'] - c['in']:5.2f}s)  xfade depois: {c['xf']}")
        print(f"{len(P)} clipes, {sum(c['out'] - c['in'] for c in P):.1f}s")
        sys.exit()

    fc = FC()
    seq = fc.run("sequence.inspect")
    v1 = {i["clip"]: i for t in seq["video"] if t["name"] == "Video 1" for i in t["items"]}
    a1 = next(t for t in seq["audio"] if t["name"] == "Audio 1")
    link = {i["link"]: i["clip"] for i in a1["items"] if i.get("link") is not None}
    keep = v1[KEEP_LAST_2349]
    rm = REMOVE_2349 + [link[v1[c]["link"]] for c in REMOVE_2349 if v1[c].get("link") in link] + RAW
    # 1) transcript + source markers on C2351
    fc.run("transcript.set", item=ITEM, transcript={"language": "pt", "speakers": [{"name": "Hugo"}], "words": [
        {"text": w["text"], "start": round(w["start"] * T), "end": round(max(w["end"], w["start"]) * T), "speaker": 0}
        for w in words if w["text"]]})
    fc.run("source.open", item=ITEM)
    for a, b, color, label, comment, _ in BLOCKS:
        fc.run("markers.add", target="source", time=round(a * T), durationFrames=max(1, round((b - a) * FPS)),
               name=label, comment=comment, color=color)
    # 2) drop the markers that belonged to the old ending
    for mk in [x for x in seq["markers"] if x["name"].startswith(OLD_MARKERS)]:
        fc.run("playhead.set", time=mk["start"])
        fc.run("markers.clearCurrent", target="program")
    # 3) clear the old C2349 ending + raw C2351, then place the new takes after clip 766
    fc.run("edit.clear", clips=rm)
    pos = round(keep["end"] / FRAME)
    placed, new_markers = [], []
    for c in P:
        fin, n = round(c["in"] * FPS), round(c["out"] * FPS) - round(c["in"] * FPS)
        r = fc.run("timeline.place", item=ITEM, track="V1", audioTrack="A1", time=pos * FRAME,
                   sourceIn=fin * FRAME, duration=n * FRAME, insert=False)
        placed.append(r["clips"])
        for where, name, color, comment in c["markers"]:
            new_markers.append(dict(time=(pos if where == "start" else pos + n - 1) * FRAME, name=name, color=color, comment=comment))
        pos += n
    for mk in new_markers:
        fc.run("markers.add", target="program", **mk)
    # 4) crossfades: junction (C2349 '…sessenta mil reais.' -> 'Você leva…') is a sentence boundary, then the plan's
    a1 = next(t for t in fc.run("sequence.inspect")["audio"] if t["name"] == "Audio 1")
    items = a1["items"]
    keep_a = next(i for i in items if i.get("link") == keep.get("link") and i["item"] == 6)
    chain = [keep_a] + [i for i in items if i["item"] == ITEM]
    xf = [m.XF_BOUNDARY] + [c["xf"] for c in P]
    n_xf = 0
    for k, (c, nx) in enumerate(zip(chain, chain[1:])):
        if c["endFrame"] == nx["startFrame"] and xf[k]:
            fc.run("sequence.applyAudioTransition", clip=c["clip"], edge="out", effect="constant_power", frames=xf[k])
            n_xf += 1
    print(f"removidos {len(rm)} clipes; colocados {len(P)} takes do C2351 (fim em {m.fmt(pos / FPS)}); "
          f"{len(new_markers)} marcadores; {n_xf} crossfades")

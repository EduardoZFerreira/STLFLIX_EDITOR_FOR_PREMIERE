"""Decupagem + assembly of C2347/C2348/C2349 with the user's measured style:
head = speech onset - 2 f, tail = speech offset + 5.5 f (audio energy, not Whisper times),
internal pauses >= 0.3 s removed, crossfades 3 f mid-sentence / 10 f at sentence boundaries.

Usage: python montar_corpo2.py plan            -> print the cut plan and boundary warnings
       python montar_corpo2.py jsonl out.jsonl -> FilmCraft commands (transcripts, source markers,
                                                  clear raw clips, place clips, sequence markers)
       python montar_corpo2.py xfades          -> apply the audio crossfades in the live app
"""
import json, os, sys, wave
import numpy as np

T, FPS = 254_016_000_000, 24000 / 1001
FRAME = 10_594_584_000
HEAD_F, TAIL_F, MIN_PAUSE = 2.0, 5.5, 0.30
XF_MID, XF_BOUNDARY = 3, 10
USE, ALT, DROP, NOTE = "Green", "Yellow", "Rose", "Blue"
HERE = os.path.dirname(os.path.abspath(__file__))

# --- takes: (a', b') are safe outer bounds placed in silence; USE entries carry optional sequence markers
# markers: list of (where "start"|"end", name, color, comment)
FILES = {
    "C2347": {"item": 4, "raw": [490, 491], "blocks": [
        (0.0, 2.6, NOTE, "Conversa antes de gravar", "", []),
        (6.10, 11.28, ALT, "Com essa lição… Joinville (já usado do C2346)",
         "Versão completa da frase; a montagem usa o fim do C2346 + 'e aí ele montou um expositor…' daqui.", []),
        (11.35, 23.0, USE, "Expositor + lojas de lembrancinhas + 100/300 ímãs", "", []),
        (25.0, 35.90, USE, "Petare (parte 1)", "Falou 'participou do reality show Como Vender Impressão 3D'.", []),
        (35.95, 41.20, DROP, "'Em que a gente visita…' (2 tentativas)", "", []),
        (42.0, 52.3, USE, "Petare (parte 2): 13 → 21 mil", "", [
            ("end", "TELA: Cotrim entregando os ímãs + placa do Petare", "Lavender", "")]),
        (55.3, 75.2, USE, "Fecho do Caminho 2 + ponte p/ Tales", "Ad-lib: 'Agora pensa comigo'.", []),
        (79.3, 95.2, USE, "Caminho 3 · TikTok Shop", "Abre com 'E esse caminho é o TikTok Shop' (copy: 'O terceiro caminho'). 'Todo dia' (copy: 'todo santo dia').", [
            ("start", "CAMINHO 3 · TikTok Shop (Tales)", "Blue", ""),
            ("start", "Conferir: abertura do Caminho 3", "Mango", "Ouvi 'E esse caminho é o TikTok Shop'; a copy diz 'O terceiro caminho é o TikTok Shop'.")]),
        (98.6, 106.2, USE, "Assiste, se interessa e compra", "", []),
        (107.5, 127.4, USE, "Quem não gosta de gravar + licença comercial", "Falou 'a estrela é a impressão' (copy: 'a peça').", []),
        (128.0, 182.95, USE, "Tales: começo difícil → ultimato → 43 produtos", "", []),
        (182.96, 191.5, DROP, "'E aí ele começou lives…' take 1", "", []),
        (191.8, 202.2, USE, "Lives com 30% de margem, R$ 400–500", "Transcrição ouviu '30% de IMAGEM' duas vezes.", [
            ("start", "Conferir: '30% de margem'", "Mango", "A transcrição ouviu '30% de imagem'. Ouvir se ele disse 'margem'.")]),
        (202.90, 229.6, DROP, "'E esse foi o caminho…' takes 1–2", "", []),
        (229.7, 243.62, USE, "Impulsionado pela plataforma: benefícios", "", []),
        (243.65, 245.86, DROP, "'Isenção de taxa pelos próprios'", "", []),
        (246.3, 251.70, USE, "Isenção 60 dias + créditos de tráfego", "", []),
        (251.72, 265.32, DROP, "'Imagina…' take 1 + 'não tinha salvação'", "", []),
        (266.1, 290.3, USE, "Imagina… 3 vídeos de 30s + Shopee + onda", "", []),
        (291.9, 304.60, USE, "Ana: Elite 3D, 90 pedidos/dia", "", [
            ("start", "Conferir: números da Ana", "Mango",
             "Falou 'mais de 400 unidades' (copy: 413) e 'isso é só com o incensário' logo depois dos 90 pedidos/dia.")]),
        (304.65, 309.02, ALT, "'E isso é só com o incensário' (take 1)", "", []),
        (310.8, 319.1, USE, "Incensário: mais de 400 unidades", "", [
            ("end", "TELA: live do Tales + painel da Ana", "Lavender", "")]),
        (320.54, 325.82, DROP, "Piada 'sem encher a empresa de fumaça'", "", []),
    ]},
    "C2348": {"item": 5, "raw": [493, 494], "blocks": [
        (1.5, 18.3, USE, "Fecho do Caminho 3 + ponte p/ o quarto caminho", "", []),
        (23.3, 33.15, USE, "Caminho 4 · Feira", "", [("start", "CAMINHO 4 · Feiras (Michelle e Adriano)", "Blue", "")]),
        (33.20, 39.60, ALT, "'Como na feira…' (take 1)", "Texto igual à copy ('Como NA feira'); o take 2 diz 'Como A feira'.", []),
        (42.3, 50.8, USE, "Sem comissão: até 10x + maior margem", "", []),
        (50.92, 60.36, DROP, "'E quem mostra isso…' + 'mentoradas'", "", []),
        (60.44, 65.84, USE, "Michelle e Adriano", "", []),
        (65.92, 70.44, DROP, "'Eles são o casal…' (2 tentativas)", "", []),
        (70.9, 91.24, USE, "Casal de SC → 1ª feira R$ 300 → feiras maiores", "Ad-lib: 'Pode não parecer muito'.", []),
        (91.34, 97.48, DROP, "'Hoje eles fazem…' take 1 ('pegam')", "", []),
        (100.9, 109.10, USE, "4 a 8 feiras/mês, R$ 600 no espaço, 6–7 mil", "", []),
        (109.18, 126.66, DROP, "'Melhor mês' take 1 + 'mais amanteigado'", "", []),
        (127.3, 134.8, USE, "Melhor mês: R$ 52 mil", "", []),
        (135.2, 156.2, USE, "Emerson: Uber → 1ª impressora", "", []),
        (156.78, 173.38, DROP, "Sagrada Família take 1 ('cada pecha')", "", []),
        (174.4, 190.0, USE, "Emerson: Sagrada Família, ~R$ 60 de lucro", "", [
            ("end", "TELA: banca da Michelle e do Adriano + Emerson", "Lavender", "Banca da Michelle e do Adriano + Emerson com as miniaturas.")]),
        (194.1, 205.3, USE, "Fecho do Caminho 4", "Falou 'pode ser UM caminho' (copy: 'o seu caminho').", []),
        (207.24, 210.20, NOTE, "Recado: fechamento dos caminhos", "", []),
        (211.5, 249.3, USE, "Fechamento dos caminhos", "", [("start", "FECHAMENTO DOS CAMINHOS", "Blue", "")]),
        (249.72, 255.16, DROP, "Conversa / pausa", "", []),
    ]},
    "C2349": {"item": 6, "raw": [496, 497], "blocks": [
        (0.8, 16.9, USE, "As 4 respostas + Black November", "", [
            ("start", "OFERTA · Black November", "Blue", ""),
            ("end", "TELA: lettering 'Black November'", "Lavender", "")]),
        (17.5, 36.5, USE, "O que vender: STLFLIX + STLIA", "", []),
        (37.8, 43.14, USE, "Por quanto vender: STLSeller", "", []),
        (43.28, 48.80, ALT, "'Ele mostra…' (take 1)", "", []),
        (51.9, 61.2, USE, "STLSeller: preço, conta da saboneteira, anúncio", "Falou 'o que VOCÊ está vendendo' (copy: 'o que está vendendo').", [
            ("start", "Conferir: STLSeller 'o que você está vendendo'", "Mango",
             "A copy diz 'mostra o que está vendendo'; ele disse 'o que você está vendendo', que muda o sentido.")]),
        (62.54, 87.60, DROP, "'As duas últimas respostas' take 1 + 'mais manteiga'", "", []),
        (89.6, 103.6, USE, "Onde e como vender: formações", "", []),
        (103.62, 105.74, DROP, "'Pra você vender no Marketplace' take 1", "", []),
        (106.5, 121.0, USE, "Formações: Luan, Cotrim, Tales, Michelle", "", [
            ("start", "AJUSTAR: nomes oficiais das formações", "Mango", "Pendência da copy: nomes oficiais das formações do Cotrim, do Tales e da Michelle.")]),
        (122.46, 163.74, DROP, "STLAcademy takes 1–2 + 'não é mais Fusion 360'", "", []),
        (164.5, 174.4, USE, "STLAcademy: 7 cursos, Impressão Sem Medo, Fusion", "", [
            ("end", "TELA: as plataformas e as capas das formações", "Lavender", "")]),
        (178.6, 194.4, USE, "Assinatura x vitalício: voltou", "", [
            ("end", "TELA: fundo escuro, lettering 'VITALÍCIO'", "Lavender", "")]),
        (199.90, 219.52, DROP, "'Ou seja, você paga uma vez' takes 1–2", "", []),
        (220.3, 230.7, USE, "Paga uma vez, acesso pra sempre: o que inclui", "", []),
        (230.96, 233.80, DROP, "'Assim, hoje você começa…' take 1", "", []),
        (235.7, 263.8, USE, "Um caminho por vez + como a STLFLIX oferece vitalício", "", []),
        (268.7, 278.9, USE, "Quanto vale: R$ 9.190", "", [("start", "INVESTIMENTO E CASHBACK", "Blue", "")]),
        (279.34, 291.10, DROP, "'Mas você não vai fazer só isso' take 1", "", []),
        (291.9, 310.9, USE, "Cursos inéditos: R$ 15.186 → 4 anos: R$ 60 mil", "", [
            ("end", "TELA: '1 ano: R$ 15.186 · 4 anos: R$ 60.744'", "Lavender", "")]),
        (313.64, 329.48, DROP, "Investimento takes 1–2 (erro de valor, sem parcela)", "", []),
        (331.30, 371.16, NOTE, "Conversa: valor da parcela ('12 de 497')", "", []),
        (373.3, 387.7, USE, "Investimento: R$ 4.997 ou 12x", "", [
            ("start", "Conferir: PARCELA 12x de R$ 497?", "Mango",
             "Hugo falou '12 vezes de 4-9-7' (combinado no set). A copy diz 'Valor parcela: 12 vezes de 490'."),
            ("end", "TELA: 'R$ 4.997 à vista ou 12x de R$ …'", "Lavender", "")]),
        (390.6, 407.3, USE, "Referência: feira 6–7 mil, Cotrim já pagou o vitalício", "", []),
        (409.16, 416.92, DROP, "'E tem mais' take 1 ('deixa eu fazer certinho')", "", []),
        (417.4, 428.35, USE, "Cashback em cupons de filamento (12 meses)", "", [
            ("end", "FALTA: explicação dos cupons", "Mango",
             "A gravação para em 'liberados ao longo de 12 meses'. Copy: 334 cupons de R$ 15. Gravar ou cobrir com tela.")]),
        (428.62, 445.92, NOTE, "Faltou a info dos cupons ('aí fudeu') + pausa", "", []),
    ]},
}


def load(name):
    with wave.open(os.path.join(HERE, f"{name}.wav"), "rb") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    hop = 160  # 10 ms
    rms = np.sqrt(np.convolve(x * x, np.ones(hop) / hop, mode="same"))[::hop]
    db = 20 * np.log10(rms + 1e-9)
    mask = db > np.percentile(db, 10) + 18
    words = json.load(open(os.path.join(HERE, f"{name}.transcript.json"), encoding="utf-8"))["words"]
    return (mask, db), words


def quietest(db, t, before=0.35, after=0.05):
    """Time of the quietest 10 ms frame in [t - before, t + after]."""
    i0, i1 = int(round((t - before) * 100)), int(round((t + after) * 100))
    return (i0 + int(np.argmin(db[i0:i1]))) / 100


def refine(md, a, b):
    """Split [a, b] into clips around speech islands; returns (clips, warnings)."""
    mask, db = md
    warn = []
    i0, i1 = int(round(a * 100)), int(round(b * 100))
    if mask[i0:i0 + 3].any():
        a = quietest(db, a, before=0.05, after=0.35)
        warn.append(f"início dentro da fala: cortado no ponto mais baixo ({a:.2f}s)")
    if mask[i1 - 3:i1].any():
        b = quietest(db, b)
        warn.append(f"fim dentro da fala: cortado no ponto mais baixo ({b:.2f}s)")
    i0, i1 = int(round(a * 100)), int(round(b * 100))
    seg = mask[i0:i1]
    idx = np.flatnonzero(seg)
    if idx.size == 0:
        return [], ["sem fala"]
    islands, s, prev = [], idx[0], idx[0]
    for k in idx[1:]:
        if (k - prev) / 100 >= 0.10:
            islands.append((s, prev + 1)); s = k
        prev = k
    islands.append((s, prev + 1))
    islands = [(i0 + x, i0 + y) for x, y in islands if (y - x) >= 6]  # ignore clicks < 60 ms
    clips = []
    for on, off in islands:
        st = max(a, on / 100 - HEAD_F / FPS)
        en = min(b, off / 100 + TAIL_F / FPS)
        if clips and st - clips[-1][1] < MIN_PAUSE:  # removed part must be >= 0.3 s
            clips[-1] = (clips[-1][0], en)
        else:
            clips.append((st, en))
    return clips, warn


def is_boundary(words, t):
    prev = [w for w in words if w["end"] <= t + 0.05]
    nxt = [w for w in words if w["start"] >= t - 0.05]
    p = prev[-1]["text"] if prev else ""
    n = nxt[0]["text"] if nxt else ""
    gap = (nxt[0]["start"] - prev[-1]["end"]) if prev and nxt else 0
    return p.endswith((".", "?", "!")) or (n[:1].isupper() and not p.endswith(",") and gap >= 0.5)


def plan():
    out = []  # (file, item, src_in, src_out, take_name, xfade_after, markers_for_this_clip)
    for name, cfg in FILES.items():
        mask, words = load(name)
        for a, b, color, label, _, marks in cfg["blocks"]:
            if color != USE:
                continue
            clips, warn = refine(mask, a, b)
            for k, (s, e) in enumerate(clips):
                m = [x for x in marks if (x[0] == "start" and k == 0) or (x[0] == "end" and k == len(clips) - 1)]
                out.append({"file": name, "item": cfg["item"], "in": s, "out": e, "take": label, "first": k == 0,
                            "markers": m, "warn": warn if k == 0 else [], "words": words})
    for i, c in enumerate(out):
        nxt = out[i + 1] if i + 1 < len(out) else None
        if nxt is None:
            c["xf"] = None
        elif nxt["file"] != c["file"] or nxt["first"]:
            c["xf"] = XF_BOUNDARY if is_boundary(c["words"], c["out"]) else XF_MID
        else:
            c["xf"] = XF_BOUNDARY if is_boundary(c["words"], (c["out"] + nxt["in"]) / 2) else XF_MID
    return out


def fmt(s):
    return f"{int(s // 60)}:{s % 60:05.2f}"


if __name__ == "__main__":
    mode = sys.argv[1]
    P = plan()
    if mode == "plan":
        cur = None
        for c in P:
            if c["first"]:
                print(f"{c['file']} {c['take']}" + (f"   ⚠ {', '.join(c['warn'])}" if c["warn"] else ""))
            print(f"    {fmt(c['in'])}-{fmt(c['out'])} ({c['out'] - c['in']:5.2f}s)  xfade depois: {c['xf']}")
        total = sum(c["out"] - c["in"] for c in P)
        print(f"{len(P)} clipes, {total / 60:.1f} min; crossfades 3q: {sum(1 for c in P if c['xf'] == 3)}, 10q: {sum(1 for c in P if c['xf'] == 10)}")
    elif mode == "jsonl":
        sys.path.insert(0, HERE)
        from fc import FC
        seq = FC().run("sequence.inspect")
        v1 = [i for t in seq["video"] if t["name"] == "Video 1" for i in t["items"] if i["item"] == 3]
        pos = round(v1[-1]["end"] / FRAME)  # butt against the end of C2346
        cmds = []
        for name, cfg in FILES.items():
            words = json.load(open(os.path.join(HERE, f"{name}.transcript.json"), encoding="utf-8"))["words"]
            cmds.append({"id": "transcript.set", "params": {"item": cfg["item"], "transcript": {
                "language": "pt", "speakers": [{"name": "Hugo"}],
                "words": [{"text": w["text"], "start": round(w["start"] * T), "end": round(max(w["end"], w["start"]) * T), "speaker": 0}
                          for w in words if w["text"]]}}})
            cmds.append({"id": "source.open", "params": {"item": cfg["item"]}})
            for a, b, color, label, comment, _ in cfg["blocks"]:
                cmds.append({"id": "markers.add", "params": {"target": "source", "time": round(a * T),
                             "durationFrames": max(1, round((b - a) * FPS)), "name": label, "comment": comment, "color": color}})
        cmds.append({"id": "edit.clear", "params": {"clips": [c for cfg in FILES.values() for c in cfg["raw"]]}})
        seq_markers = []
        for c in P:
            fin, fout = round(c["in"] * FPS), round(c["out"] * FPS)
            n = fout - fin
            cmds.append({"id": "timeline.place", "params": {"item": c["item"], "track": "V1", "audioTrack": "A1",
                         "time": pos * FRAME, "sourceIn": fin * FRAME, "duration": n * FRAME, "insert": False}})
            for where, mname, mcolor, mcomment in c["markers"]:
                seq_markers.append({"time": (pos if where == "start" else pos + n - 1) * FRAME,
                                    "name": mname, "color": mcolor, "comment": mcomment})
            pos += n
        for m in seq_markers:
            cmds.append({"id": "markers.add", "params": {"target": "program", **m}})
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            for c in cmds:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"{len(cmds)} comandos -> {sys.argv[2]} (início em {fmt(round(v1[-1]['end'] / FRAME) / FPS)})")
    elif mode == "xfades":
        sys.path.insert(0, HERE)
        from fc import FC
        fc = FC()
        a1 = next(t for t in fc.run("sequence.inspect")["audio"] if t["name"] == "Audio 1")
        items = [i for i in a1["items"]]
        # the C2346 -> C2347 junction plus every butt cut inside the new material, in timeline order
        new = [i for i in items if i["item"] in (4, 5, 6)]
        last2346 = [i for i in items if i["item"] == 3][-1]
        chain = [last2346] + new
        xf = [XF_MID] + [c["xf"] for c in P]  # junction 'Joinville, | e aí ele montou' is mid-sentence
        done = 0
        for k, (c, nx) in enumerate(zip(chain, chain[1:])):
            if c["endFrame"] != nx["startFrame"] or xf[k] is None:
                continue
            fc.run("sequence.applyAudioTransition", clip=c["clip"], edge="out", effect="constant_power", frames=xf[k])
            done += 1
        print(f"crossfades aplicados: {done}")

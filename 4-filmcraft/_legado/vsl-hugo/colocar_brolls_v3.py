"""Place the 13 matched B-rolls on V3 at the Hugo line they illustrate (video copied from the already-reframed
block pieces, so the 9:16 keyframes come along); 'Vídeo direto' also gets its audio on A3 (track muted).
Usage: python colocar_brolls_v3.py plan|apply
"""
import difflib, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
HERE = os.path.dirname(os.path.abspath(__file__))
CAM = {1: "C2351", 2: "C2345", 3: "C2346", 4: "C2347", 5: "C2348", 6: "C2349"}

# (#, uso, Hugo start phrase, Hugo end phrase (citação) | None, B-roll file, B-roll start phrase, B-roll end phrase (direto) | None)
ITEMS = [
    # (#, uso, Hugo phrase start, Hugo phrase end, near (s), B-roll file, B-roll start phrase, B-roll end phrase)
    (3, "Citação", "mas para deixar a disputa justa", "que ele ja vendia", 550, "Arena 3D - EP2", "eu vou criar o meu primeiro anuncio", None),
    (4, "Citação", "o luan tentava responder 3 perguntas", "com esse produto", 560, "Arena 3D - EP2 - STL Seller", "entao a minha meta querendo ou nao", None),
    (5, "Citação", "entao nas primeiras vendas colocou", "nome do cliente", 574, "Arena 3D - EP3", "voce ta saindo no zero", None),
    (6, "Vídeo direto", "a primeira venda saiu no sexto dia", "3 produtos de 1 vez", 582, "Arena 3D - EP3", "nossa primeira venda", "venda tripla"),
    (7, "Vídeo direto", "em 1 semana e meia a loja", "8 avaliacoes 5 estrelas", 586, "Arena 3D - EP5 - Kit Leão", "e eu estou vendo aqui que voce ja esta com avaliacao", "que impressa 3d como chaveirinha"),
    (22, "Vídeo direto", "chegou a ser expulso de 1 shopping", "expulso de 1 shopping", 672, "Arena 3D EP 01 - Teaser", "hoje fui expulso do shopping", "hoje fui expulso do shopping"),
    (25, "Citação", "alem disso ele foi aprender com o", "de faturamento por mes", 701, "Higor - Chapada Diamantina", None, None),
    (26, "Vídeo direto", "ele voltou com 1 das licoes mais importantes", "para o lojista vender", 709, "Arena 3D - EP7", "do que o proprio produto sao as ferramentas", "vender esse produto"),
    (27, "Vídeo direto", "com essa licao o cotrim criou com a", "lojas de lembrancinhas", 717, "Arena 3D - EP7", "to rodando uns testezinhos aqui", "temática joinville"),
    (11, "Vídeo direto", "na primeira live ele passou 1 hora", "nao vendeu nada", 818, "Arena 3D - EP2", "corri agora ali comprei os incensos", "incensarizinho"),
    (16, "Citação", "so que a margem dessas vendas estava baixa", "inclusos nisso", 855, "Arena 3D - EP7", "20 pedidos", None),
    (18, "Vídeo direto", "lives com 30", "que ele foi desenvolvendo", 861, "Arena 3D - EP7", "teve 500 reais de gmv", "39 novos seguidores"),
    (19, "Vídeo direto", "e isso so com o incensario da", "400 unidades desse produto", 924, "Arena 3D - EP3", "mais de 400 eu acho", "403 divididos"),
]
PAD_HEAD, PAD_TAIL = 0.15, 0.5   # around the B-roll speech for 'Vídeo direto'


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    rep = {"pra": "para", "pro": "para", "um": "1", "uma": "1", "steliflix": "stlflix", "thales": "tales"}
    return [rep.get(t, t) for t in re.findall(r"[a-z0-9]+", s.replace("stl flix", "stlflix"))]


def find(tokens, phrase, after=-1.0, before=1e9):
    q = norm(phrase)
    best = (0.0, None)
    for i in range(len(tokens) - len(q) + 1):
        if not (after <= tokens[i][1] <= before):
            continue
        r = difflib.SequenceMatcher(None, " ".join(q), " ".join(t for t, *_ in tokens[i:i + len(q)])).ratio()
        if r > best[0]:
            best = (r, i)
    return best[1], best[0], len(q)


fc = FC()
seq = fc.run("sequence.inspect")
v1 = [c for t in seq["video"] if t["name"] == "Video 1" for c in t["items"]]
hw, cache = [], {}
for c in v1:
    if c["item"] not in CAM:
        continue
    nm = CAM[c["item"]]
    cache.setdefault(nm, json.load(open(os.path.join(HERE, f"{nm}.transcript.json"), encoding="utf-8"))["words"])
    a, b = c["sourceIn"] / T, c["sourceOut"] / T
    for w in cache[nm]:
        if w["end"] > a + 0.1 and w["start"] < b - 0.1:
            s0 = c["start"] / T + max(0.0, w["start"] - a)
            e0 = c["start"] / T + (min(w["end"], b) - a)
            for tok in norm(w["text"]):
                hw.append((tok, s0, e0))
hw.sort(key=lambda x: x[1])
hugo_end = max(c["end"] for c in v1 if c["item"] in CAM) / T
status = {m["name"]: m["item"] for m in fc.run("media.status")}
pieces_all = [c for t in seq["video"] for c in t["items"] if c["start"] / T > hugo_end + 1]

plan = []
for num, uso, h_a, h_b, near, src, b_a, b_b in ITEMS:
    i, r, n = find(hw, h_a, after=near - 20, before=near + 20)
    t_start = hw[i][1]
    j, r2, n2 = find(hw, h_b, after=t_start, before=t_start + 25)
    t_end = hw[j + n2 - 1][2]
    if uso == "Citação":
        dur = t_end - t_start + 0.2
    tr = json.load(open(os.path.join(HERE, "broll", "tr_" + src.replace(" ", "_") + ".json"), encoding="utf-8"))
    bw = [(tok, w["start"], w["end"]) for w in tr["words"] for tok in norm(w["text"])]
    if b_a:
        k, rb, nb = find(bw, b_a)
        s_a = max(0.0, bw[k][1] - PAD_HEAD)
    else:
        rb, s_a = 1.0, 2.6            # Higor: start on the shot with Higor and Cotrim in the shop
    if uso == "Vídeo direto":
        k2, rb2, nb2 = find(bw, b_b, after=s_a, before=s_a + 30)
        dur = bw[k2 + nb2 - 1][2] + PAD_TAIL - s_a
    item = status[src + ".mp4"]
    piece = next((c for c in pieces_all if c["item"] == item and c["sourceIn"] / T - 0.05 <= s_a and s_a + dur <= c["sourceOut"] / T + 0.05), None)
    t_place = t_start if uso == "Citação" else t_end + 0.05     # 'Vídeo direto' enters right after the line
    plan.append(dict(num=num, uso=uso, t=t_place, dur=dur, src=src, s_a=s_a, item=item, piece=piece, conf=(round(r, 2), round(rb, 2))))
plan.sort(key=lambda p: p["t"])
for k in range(len(plan) - 1):             # no overlaps on V3: trim a citação, push after a vídeo direto
    p, q = plan[k], plan[k + 1]
    if p["t"] + p["dur"] > q["t"] - 0.05:
        if p["uso"] == "Citação":
            p["dur"], p["trimmed"] = q["t"] - 0.05 - p["t"], True
        else:
            q["shift"] = round(p["t"] + p["dur"] + 0.05 - q["t"], 2)
            q["t"] = p["t"] + p["dur"] + 0.05


def fmt(s):
    return f"{int(s // 60)}:{s % 60:05.2f}"


if __name__ == "__main__":
    for p in plan:
        print(f"#{p['num']:02d} {p['uso']:12s} V3 {fmt(p['t'])}–{fmt(p['t'] + p['dur'])} ({p['dur']:4.1f}s{' encurtado' if p.get('trimmed') else ''}{f" empurrado +{p['shift']}s" if p.get('shift') else ''}) "
              f"← {p['src'][:26]:26s} src {fmt(p['s_a'])} | conf {p['conf']} | pedaço do bloco: {'ok' if p['piece'] else 'NÃO ENCONTRADO'}")
    if sys.argv[1] != "apply":
        sys.exit()
    tmp = None
    for p in plan:
        pc = p["piece"]
        f_a, n = round(p["s_a"] * FPS), max(1, round(p["dur"] * FPS))
        target = round(p["t"] * FPS)
        offset = f_a - round(pc["sourceIn"] / FRAME)
        park = max(0, target - offset)
        r = fc.run("timeline.move", moves=[{"clip": pc["clip"], "track": tmp or "new", "time": park * FRAME}], insert=False, linked=False, copy=True)
        cid = r["copied"][0]
        if tmp is None:
            tmp = next(t["id"] for t in fc.run("sequence.inspect")["video"] if any(c["clip"] == cid for c in t["items"]))
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        head = f_a * FRAME - c["sourceIn"]
        if head:
            fc.run("timeline.trim", clip=cid, edge="in", mode="regular", delta=head)
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        tail = (c["end"] - c["start"]) - n * FRAME
        if tail:
            fc.run("timeline.trim", clip=cid, edge="out", mode="regular", delta=-tail)
        fc.run("timeline.move", moves=[{"clip": cid, "track": "V3", "time": target * FRAME}], insert=False, linked=False)
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        if p["uso"] == "Vídeo direto":
            fc.run("timeline.place", item=p["item"], track="A3", time=target * FRAME, sourceIn=f_a * FRAME, duration=n * FRAME, insert=False, video=False)
        print(f"#{p['num']:02d} na V3 em {fmt(c['start'] / T)} src {fmt(c['sourceIn'] / T)}–{fmt(c['sourceOut'] / T)}")
    fc.run("sequence.deleteTracks", video="empty")
    fc.run("mixer.setStrip", strip="A3", mute=True)
    print("trilha temporária removida · A3 mutada")

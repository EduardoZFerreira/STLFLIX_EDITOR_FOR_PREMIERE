"""VSL-Shark body: place the 145 HyperFrames motions (vsl-shark-corpo/renders/cenas, B02A..B30F) on V2 of
"Corpo decupado sem cross fade", each where Lincoln says what the motion shows.

Matching: each scene's on-screen text (parsed from build.mjs: T/L/K/N/TT/VX/CTA, topo, caminho) is compared with
the Whisper words of the sequence (shark/Corpo.json), only inside the scene's script block (B05x -> Bloco 5, block
starts from Transcricao_Shark_Corpo.md). Score = IDF-weighted share of the scene's words heard in the next ~7 s,
first-phase words count double. Inside a block the scenes keep their A, B, C order (DP, >= 1.5 s apart).
Placement like the leads: start LEAD_IN before the matched word, scale 200 on V2; a scene that would run into the
next keeps its head plus the last FADE s.

Usage: python motions_corpo.py plan            -> table + low-confidence list (no app needed)
       python motions_corpo.py apply           -> live app (filmcraft --control 9876)
Env CORPO_SEQ / CORPO_TR / CORPO_CLIPS / CORPO_MD / CORPO_PLAN point it at another body sequence (e.g. the short cut).
"""
import json, math, os, re, sys, unicodedata, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
HERE = os.path.dirname(os.path.abspath(__file__))
HF = r"C:\Users\joaop\OneDrive\Desktop\Hyperframes\videos\vsl-shark-corpo"
CENAS = os.path.join(HF, "renders", "cenas")
MD = os.environ.get("CORPO_MD", r"C:\Users\joaop\OneDrive\Desktop\Filmcraft\Transcricoes\Transcricao_Shark_Corpo.md")
SEQ_NAME = os.environ.get("CORPO_SEQ", "Corpo decupado sem cross fade")
LEAD_IN, FADE, GAP, WIN, MIN_SEP = 0.2, 0.5, 0.1, 7.0, 1.5
# scenes whose on-screen words also appear in an earlier line: pin them to the spoken phrase (checked by hand)
PIN = {"B04B": "o luan ja vivia", "B27B": "a gente esta colocando 1 gerenciador", "B28C": "tudo isso esta nessa oferta",
       "B30F": ["clica no botao aqui embaixo", "clica no link abaixo"]}
# scenes to leave out in a given cut (comma list), e.g. lines that a shorter version dropped but that fuzzy-match
EXCLUDE = set(x for x in os.environ.get("CORPO_EXCLUDE", "").split(",") if x)
STOP = set("a o e de da do das dos que pra para com um uma na no em por se ele ela isso esse essa os as ja mais so nao foi "
           "voce sua seu suas seus eu me mas como tem ter tinha the ao aos pelo pela nos nas ou ate tudo todo toda muito".split())
NUM = {"um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "quatro": "4", "cinco": "5", "seis": "6", "sete": "7",
       "oito": "8", "nove": "9", "dez": "10", "vinte": "20", "trinta": "30", "cem": "100", "pra": "para", "pro": "para",
       "steliflix": "stlflix", "thales": "tales", "luana": "luan", "higor": "igor", "stla": "stlia"}


def norm(text):
    t = unicodedata.normalize("NFKD", text.lower().replace("**", ""))
    t = "".join(c for c in t if not unicodedata.combining(c)).replace("r$", " ").replace("stl flix", "stlflix")
    return [NUM.get(x, x) for x in re.findall(r"[a-z0-9]+", t)]


def scenes():
    src = open(os.path.join(HF, "build.mjs"), encoding="utf-8").read()
    parts = re.split(r'(?=\{ id: "B\d\d[A-Z]+")', src)
    out = []
    for p in parts[1:]:
        m = re.match(r'\{ id: "(B(\d\d)[A-Z]+)", nome: "([^"]*)", dur: ([\d.]+)', p)
        if not m:
            continue
        body = p.split("\n  {")[0]
        texts = re.findall(r'\b(?:T|L|K|N|TT|VX|CTA)\("([^"]*)"', body)
        topo = re.findall(r'topo: "([^"]*)"', body)
        cam = re.findall(r'caminho\((\d+), "([^"]*)"', body)
        first = body.split("P(")[1] if "P(" in body else body
        first_texts = re.findall(r'\b(?:T|L|K|N|TT|VX|CTA)\("([^"]*)"', first.split("]")[0]) if "P(" in body else texts[:2]
        words = norm(" ".join(texts + topo + [f"caminho {a} {b}" for a, b in cam] + [m.group(3)]))
        out.append(dict(id=m.group(1), block=int(m.group(2)), nome=m.group(3), dur=float(m.group(4)),
                        kw=[w for w in words if w not in STOP], first=[w for w in norm(" ".join(first_texts + topo)) if w not in STOP]))
    return out


SKIPPED = []                                                   # (id, nome, why) of scenes left out
MIN_SCORE = float(os.environ.get("CORPO_MIN_SCORE", "0"))      # > 0 drops scenes whose line isn't in a shorter cut


def block_starts():
    starts = {}
    for line in open(MD, encoding="utf-8"):
        m = re.match(r"## BLOCO (\d+) · .*·\s+(\d+):(\d+\.\d)", line.strip())
        if m:
            starts[int(m.group(1))] = int(m.group(2)) * 60 + float(m.group(3))
    return starts


def mov_durs():
    d = {}
    for line in open(os.path.join(HF, "renders", "cortes.txt"), encoding="utf-8"):
        a = line.split()
        if len(a) >= 3:
            d[a[2].split("-")[0]] = (a[2] + ".mov", float(a[1]))
    return d


def build_plan():
    tr = json.load(open(os.path.join(HERE, os.environ.get("CORPO_TR", "Corpo.json")), encoding="utf-8"))
    total = json.load(open(os.path.join(HERE, os.environ.get("CORPO_CLIPS", "corpo_clips.json")), encoding="utf-8"))["duration"]
    toks = [(tok, w["start"]) for w in tr["words"] for tok in norm(w["text"])]
    df = collections.Counter()
    for k in range(0, len(toks), 25):                          # document frequency over ~8 s windows
        for w in set(t for t, _ in toks[k:k + 25]):
            df[w] += 1
    ndoc = len(toks) / 25
    idf = lambda w: math.log((ndoc + 1) / (df.get(w, 0) + 0.5))
    bs = block_starts()
    order = sorted(bs)
    movs = mov_durs()
    plan = []
    by_block = collections.defaultdict(list)
    for s in scenes():
        by_block[s["block"]].append(s)
    for b in sorted(by_block):
        sc = sorted(by_block[b], key=lambda s: s["id"])
        if b not in bs:                                        # block cut from this version of the body
            SKIPPED.extend((s["id"], s["nome"], "bloco fora desta versão") for s in sc)
            continue
        a = bs[b]
        nxt = [bs[x] for x in order if bs[x] > a]
        z = min(nxt) if nxt else total
        cand = [i for i, (_, t) in enumerate(toks) if a - 0.5 <= t < z - 0.5]
        if not cand:
            continue

        def score(s, i):
            t0 = toks[i][1]
            heard = {}
            for w, t in toks[i:i + 40]:
                if t - t0 > WIN:
                    break
                heard.setdefault(w, t - t0)
            num = den = 0.0
            for w in set(s["kw"]):
                wt = idf(w) * (2.0 if w in s["first"] else 1.0)
                den += wt
                if w in heard:
                    num += wt * (1.0 - 0.06 * heard[w])          # said sooner = better
            first_hit = toks[i][0] in s["first"] or toks[i][0] in s["kw"]
            return (num / den if den else 0.0) + (0.05 if first_hit else 0.0)
        # DP: scenes in order, positions increasing and >= MIN_SEP apart
        n, m = len(sc), len(cand)
        S = [[score(s, i) for i in cand] for s in sc]
        import difflib
        for k, s in enumerate(sc):
            if s["id"] in PIN:
                phrases = PIN[s["id"]] if isinstance(PIN[s["id"]], list) else [PIN[s["id"]]]
                r = [0.0] * len(cand)
                for ph in phrases:
                    q = " ".join(norm(ph))
                    r = [max(r[x], difflib.SequenceMatcher(None, q, " ".join(t for t, _ in toks[i:i + len(q.split())])).ratio())
                         for x, i in enumerate(cand)]
                j = max(range(len(cand)), key=lambda j: r[j])
                if r[j] >= 0.8:                                # pin only when that line is really in this cut
                    S[k] = [-1e6] * len(cand)
                    S[k][j] = 1.0 + r[j]
        best = [[-1e9] * m for _ in range(n)]
        back = [[-1] * m for _ in range(n)]
        for j in range(m):
            best[0][j] = S[0][j]
        for k in range(1, n):
            run, arg, p = -1e9, -1, 0
            for j in range(m):
                while p < m and toks[cand[p]][1] <= toks[cand[j]][1] - MIN_SEP:
                    if best[k - 1][p] > run:
                        run, arg = best[k - 1][p], p
                    p += 1
                if arg >= 0:
                    best[k][j], back[k][j] = run + S[k][j], arg
        j = max(range(m), key=lambda j: best[n - 1][j])
        picks = [0] * n
        for k in range(n - 1, -1, -1):
            picks[k] = j
            j = back[k][j]
        for k, s in enumerate(sc):
            i = cand[picks[k]]
            if s["id"] in EXCLUDE:
                SKIPPED.append((s["id"], s["nome"], "excluída à mão nesta versão (fala não existe)"))
                continue
            if S[k][picks[k]] < MIN_SCORE:                     # its line was cut from this version
                SKIPPED.append((s["id"], s["nome"], f"fala não encontrada (melhor {S[k][picks[k]]:.2f})"))
                continue
            name, dur = movs[s["id"]]
            heard = " ".join(t for t, _ in toks[i:i + 10])
            plan.append(dict(id=s["id"], nome=s["nome"], name=name, dur=dur, start=max(0.0, toks[i][1] - LEAD_IN),
                             score=round(S[k][picks[k]], 2), heard=heard, block=b))
    plan.sort(key=lambda p: p["start"])
    for k, p in enumerate(plan):
        room = (plan[k + 1]["start"] - GAP - p["start"]) if k + 1 < len(plan) else (total - p["start"])
        p["len"] = min(p["dur"], room)
        p["trim"] = p["len"] < p["dur"] - 1e-6
    return plan


def mmss(s):
    return f"{int(s // 60):02d}:{s % 60:04.1f}"


if __name__ == "__main__":
    P = build_plan()
    if sys.argv[1] == "plan":
        for p in P:
            flag = "⚠" if p["score"] < 0.35 else " "
            fit = f"{p['dur']:.0f}s→{p['len']:.1f}s" if p["trim"] else f"{p['dur']:.0f}s"
            print(f"{flag}{p['id']:5s} {mmss(p['start'])} {fit:11s} {p['score']:.2f} | {p['nome'][:38]:38s} | {p['heard'][:60]}")
        low = [p for p in P if p["score"] < 0.35]
        for sid, nome, why in SKIPPED:
            print(f" ✗{sid:5s} {nome[:38]:38s} | {why}")
        print(f"{len(P)} cenas · encurtadas {sum(p['trim'] for p in P)} · baixa confiança {len(low)} · menos de 1,5 s {sum(p['len'] < 1.5 for p in P)} · fora {len(SKIPPED)}")
        json.dump(P, open(os.path.join(HERE, os.environ.get("CORPO_PLAN", "plano_corpo.json")), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        sys.exit()
    from fc import FC
    fc = FC()

    def walk(n):
        for c in n.get("children", []):
            yield c
            yield from walk(c)
    tree = fc.run("project.inspect")["root"]
    seq_id = next(c["item"] for c in walk(tree) if c.get("type") == "Sequence" and c["name"] == SEQ_NAME)
    have = {c["name"]: c["item"] for c in walk(tree) if str(c.get("name", "")).lower().endswith(".mov")}
    need = [os.path.join(CENAS, p["name"]) for p in P if p["name"] not in have]
    if need:
        fc.run("file.import", paths=need)
        have = {c["name"]: c["item"] for c in walk(fc.run("project.inspect")["root"]) if str(c.get("name", "")).lower().endswith(".mov")}
        print(f"{len(need)} motions importados")
    fc.run("sequence.open", item=seq_id)
    seq = fc.run("sequence.inspect", item=seq_id)
    v2 = next((t for t in seq["video"] if t["name"] == "Video 2"), None)
    old = [c["clip"] for c in (v2["items"] if v2 else []) if c["name"].endswith(".mov")]
    if old:
        fc.run("edit.clear", clips=old)
    placed = []
    for p in P:
        if p["len"] < 1.0:
            continue
        pos = round(p["start"] * FPS)
        segs = [(0.0, p["len"])] if not p["trim"] else [(0.0, p["len"] - FADE), (p["dur"] - FADE, p["dur"])]
        for a, b in segs:
            n = max(1, round((b - a) * FPS))
            placed += fc.run("timeline.place", item=have[p["name"]], track="V2", time=pos * FRAME, sourceIn=round(a * T),
                             duration=n * FRAME, insert=False, audio=False)["clips"]
            pos += n
    for c in (c for t in fc.run("sequence.inspect", item=seq_id)["video"] for c in t["items"] if c["clip"] in placed):
        mi = [e["effect"] for e in c["effects"]].index("motion")
        fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=200)
    print(f"{SEQ_NAME}: {len(placed)} clipes de motion na V2 ({sum(1 for p in P if p['len'] >= 1.0)} cenas)")

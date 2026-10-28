"""Cross the B-roll insertion list with (a) Hugo's timeline transcript and (b) the B-roll transcripts.
Usage: python cruzar_lista.py > cruzamento.txt"""
import difflib, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T = 254_016_000_000
HERE = os.path.dirname(os.path.abspath(__file__))
CAM = {1: "C2351", 2: "C2345", 3: "C2346", 4: "C2347", 5: "C2348", 6: "C2349"}
STOP = set("a o e de da do das dos que pra para com um uma na no em por se ele ela isso esse essa os as ja mais so nao foi".split())


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    toks = re.findall(r"[a-z0-9]+", s.replace("stl flix", "stlflix"))
    rep = {"pro": "para", "pra": "para", "steliflix": "stlflix", "stelflix": "stlflix", "igor": "higor", "thales": "tales",
           "petare": "petar", "um": "1", "uma": "1", "dois": "2", "duas": "2", "tres": "3", "dez": "10", "setenta": "70"}
    return [rep.get(t, t) for t in toks]


def tc(s):
    d = int(round(max(0.0, s) * 10))
    return f"{d // 600:02d}:{(d % 600) // 10:02d}.{d % 10}"


# --- list
raw = [l.strip() for l in open(os.path.join(HERE, "lista_brolls.txt"), encoding="utf-8") if l.strip()]
items = [dict(etapa=raw[i], fala=raw[i + 1].strip('"'), uso=raw[i + 2], fonte=raw[i + 3], cortar=raw[i + 4]) for i in range(0, len(raw), 5)]

# --- Hugo timeline words
fc = FC()
seq = fc.run("sequence.inspect")
v1 = [c for t in seq["video"] if t["name"] == "Video 1" for c in t["items"]]
hw = []
cache = {}
for c in v1:
    if c["item"] not in CAM:
        continue
    nm = CAM[c["item"]]
    cache.setdefault(nm, json.load(open(os.path.join(HERE, f"{nm}.transcript.json"), encoding="utf-8"))["words"])
    a, b = c["sourceIn"] / T, c["sourceOut"] / T
    for w in cache[nm]:
        if w["end"] > a + 0.1 and w["start"] < b - 0.1:
            for tok in norm(w["text"]):
                hw.append((tok, c["start"] / T + max(0.0, w["start"] - a)))
hw.sort(key=lambda x: x[1])
blocks = sorted([(m["start"] / T, m["name"]) for m in seq["markers"] if m.get("color") == "Blue"])


def best_window(tokens, q, step=1):
    """Best fuzzy window of len(q) tokens (content words weigh more)."""
    qs = " ".join(q)
    best = (0.0, 0)
    L = len(q)
    for i in range(0, max(1, len(tokens) - L + 1), step):
        r = difflib.SequenceMatcher(None, qs, " ".join(t for t, _ in tokens[i:i + L])).ratio()
        if r > best[0]:
            best = (r, i)
    return best


# --- B-roll transcripts (source time) + their timeline pieces
status = {m["name"]: m["item"] for m in fc.run("media.status")}
brolls = {}
for f in glob_list if (glob_list := sorted(os.listdir(os.path.join(HERE, "broll")))) else []:
    if f.startswith("tr_") and f.endswith(".json"):
        tr = json.load(open(os.path.join(HERE, "broll", f), encoding="utf-8"))
        name = f[3:-5].replace("_", " ")
        toks = [(t, w["start"]) for w in tr["words"] for t in norm(w["text"])]
        item = status.get(name + ".mp4")
        pieces = sorted([c for t in seq["video"] for c in t["items"] if c["item"] == item], key=lambda c: c["start"])
        brolls[name] = (toks, tr["words"], pieces)


def tl_of(name, t):
    for c in brolls[name][2]:
        if c["sourceIn"] / T - 0.3 <= t < c["sourceOut"] / T:
            return c["start"] / T + max(0.0, t - c["sourceIn"] / T)
    return None


def context(words, t, span=6.0):
    return " ".join(w["text"] for w in words if t - 0.5 <= w["start"] < t + span)[:140]


for k, it in enumerate(items, 1):
    q = norm(it["fala"])[:18]
    r, i = best_window(hw, q)
    blk = next((b for t, b in reversed(blocks) if t <= hw[i][1] + 0.3), "") if hw else ""
    print(f"\n#{k:02d} [{it['etapa']}] {it['uso']} · fonte: {it['fonte']} · cortar: {it['cortar']}")
    print(f"   roteiro: {it['fala'][:110]}")
    tag = "OK" if r >= 0.72 else ("PARCIAL" if r >= 0.55 else "NÃO ENCONTRADA")
    print(f"   Hugo [{tag} {r:.2f}] {tc(hw[i][1])} ({blk}): {' '.join(t for t, _ in hw[i:i + len(q)])}")
    # B-roll search: quoted 'cortar' first, else narration + description content words
    cut_q = re.findall(r'"([^"]+)"', it["cortar"])
    probes = [norm(cut_q[0])] if cut_q else []
    probes.append([t for t in norm(it["fala"] + " " + it["cortar"]) if t not in STOP][:14])
    cands = []
    for name, (toks, words, pieces) in brolls.items():
        for p in probes:
            if not p or len(toks) < 3:
                continue
            rr, ii = best_window(toks, p, step=2)
            cands.append((rr, name, toks[ii][1], words))
    cands.sort(key=lambda c: -c[0])
    for rr, name, t, words in cands[:3]:
        tl = tl_of(name, t)
        print(f"   B-roll {rr:.2f} {name} @ {tc(t)} " + (f"(timeline {tc(tl)})" if tl is not None else "(fora da timeline)") + f": {context(words, t)}")

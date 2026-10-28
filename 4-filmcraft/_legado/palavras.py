"""Hugo's words with timeline timecodes inside given windows. Usage: python palavras.py MM:SS:FF-MM:SS:FF ..."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
T, FPS = 254_016_000_000, 24000 / 1001
CAM = {1: "C2351", 2: "C2345", 3: "C2346", 4: "C2347", 5: "C2348", 6: "C2349"}
tc2s = lambda tc: (lambda m, s, f: ((m * 60 + s) * 24 + f) / FPS)(*map(int, tc.split(":")))
s2tc = lambda s: (lambda f: f"{f // 1440:02d}:{f // 24 % 60:02d}:{f % 24:02d}")(round(s * FPS))
s = FC().run("sequence.inspect")
W, cache = [], {}
for c in (c for t in s["video"] if t["name"] == "Video 1" for c in t["items"] if c["item"] in CAM):
    nm = CAM[c["item"]]
    cache.setdefault(nm, json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{nm}.transcript.json"), encoding="utf-8"))["words"])
    a, b = c["sourceIn"] / T, c["sourceOut"] / T
    W += [(c["start"] / T + max(0, w["start"] - a), w["text"].strip()) for w in cache[nm] if w["end"] > a + 0.1 and w["start"] < b - 0.1]
W.sort()
for win in sys.argv[1:]:
    a, b = map(tc2s, win.split("-"))
    print(f"== {win}\n" + " ".join(f"[{s2tc(t)[3:]}]{x}" for t, x in W if a - 0.05 <= t <= b))

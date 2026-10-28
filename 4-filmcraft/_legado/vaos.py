"""List free windows (no V2 lettering, no V3 B-roll) inside Hugo's speech, with the words spoken there."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
T, FRAME, FPS = 254016000000, 10594584000, 24000 / 1001
CAM = {1: "C2351", 2: "C2345", 3: "C2346", 4: "C2347", 5: "C2348", 6: "C2349"}
def tcode(sec):
    f = round(sec * FPS); return f"{f // 24 // 60:02d}:{f // 24 % 60:02d}:{f % 24:02d}"
fc = FC(); s = fc.run("sequence.inspect")
v1 = [c for t in s["video"] if t["name"] == "Video 1" for c in t["items"]]
words, cache = [], {}
for c in v1:
    if c["item"] not in CAM: continue
    nm = CAM[c["item"]]; cache.setdefault(nm, json.load(open(f"{nm}.transcript.json", encoding="utf-8"))["words"])
    a, b = c["sourceIn"] / T, c["sourceOut"] / T
    for w in cache[nm]:
        if w["end"] > a + 0.1 and w["start"] < b - 0.1:
            words.append((c["start"] / T + max(0, w["start"] - a), c["start"] / T + min(w["end"], b) - a, w["text"]))
words.sort()
busy = sorted([(c["start"] / T, c["end"] / T) for t in s["video"] if t["name"] in ("Video 2", "Video 3") for c in t["items"]])
end = max(c["end"] for c in v1 if c["item"] in CAM) / T
free, cur = [], 0.0
for a, b in busy:
    if a > cur: free.append((cur, min(a, end)))
    cur = max(cur, b)
if cur < end: free.append((cur, end))
blocks = sorted([(m["start"] / T, m["name"]) for m in s["markers"] if m.get("color") == "Blue"])
out = []
for a, b in free:
    if b - a < 1.5: continue
    txt = " ".join(w[2] for w in words if w[0] >= a - 0.05 and w[1] <= b + 0.05)
    blk = next((n for t, n in reversed(blocks) if t <= a + 0.1), "")
    out.append({"a": a, "b": b, "blk": blk, "txt": txt})
    print(f"{tcode(a)}–{tcode(b)} ({b - a:4.1f}s) [{blk[:22]}] {txt[:150]}")
json.dump(out, open("vaos.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(out), "vãos")

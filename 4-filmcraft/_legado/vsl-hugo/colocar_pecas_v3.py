"""Place the refined 3D-piece takes ("Peça · …" in the V1 pool) on V3 where Hugo talks about printing.
Copies the pool clip (keeping its 9:16 keyframes), takes the first `dur` of it, moves it to V3. Video only.
Usage: python colocar_pecas_v3.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC, SCRATCH

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
# (pool clip name, V3 start TC, V3 end TC (exclusive), Hugo's line)
PLAN = [
    ("Peça · tartaruga verde", "03:34:14", "03:41:08", "Essa forma de usar a impressora é ótima para aprender…"),
    ("Peça · narval (2) 1", "06:15:09", "06:18:01", "existe uma confusão sobre o que a impressão 3D vende"),
    ("Peça · polvo 1", "06:55:17", "06:59:22", "o anúncio que falava só do produto"),
    ("Peça · polvo 2", "10:36:13", "10:39:19", "colocam suas peças na prateleira e revendem"),
    ("Peça · tubarão-baleia", "13:13:10", "13:16:06", "na impressão 3D a estrela é a impressão"),
    ("Peça · bonecos e chaveiros 1", "15:33:03", "15:38:17", "ganhar muito dinheiro vendendo produtos impressos em 3D"),
    ("Peça · ornitorrinco 1", "16:51:08", "16:56:15", "revendendo as peças que o cunhado dele imprimia"),
    ("Peça · narval (2) 2", "17:11:03", "17:17:20", "se você quer vender impressão 3D e ter 10 vezes mais margem"),
]


def tc2f(tc):
    m, s, f = map(int, tc.split(":"))
    return (m * 60 + s) * 24 + f


def f2tc(f):
    return f"{f // 1440:02d}:{f // 24 % 60:02d}:{f % 24:02d}"


def clip(cid):
    return next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)


fc = FC()
seq = fc.run("sequence.inspect")
pool = {c["name"]: c for t in seq["video"] if t["name"] == "Video 1" for c in t["items"] if c["name"].startswith("Peça · ")}
busy = [(c["startFrame"], c["endFrame"]) for t in seq["video"] if t["name"] in ("Video 2", "Video 3") for c in t["items"]]
tmp, placed = None, []
for name, a_tc, b_tc, line in PLAN:
    pc = pool[name]
    target, n = tc2f(a_tc), tc2f(b_tc) - tc2f(a_tc)
    n = min(n, pc["endFrame"] - pc["startFrame"])
    clash = [(f2tc(x), f2tc(y)) for x, y in busy if x < target + n and target < y]
    if clash:
        print(f"{name}: PULADO, sobrepõe V2/V3 {clash}")
        continue
    cid = fc.run("timeline.move", moves=[{"clip": pc["clip"], "track": tmp or "new", "time": target * FRAME}],
                 insert=False, linked=False, copy=True)["copied"][0]
    if tmp is None:
        tmp = next(t["id"] for t in fc.run("sequence.inspect")["video"] if any(c["clip"] == cid for c in t["items"]))
    c = clip(cid)
    extra = (c["end"] - c["start"]) - n * FRAME
    if extra:
        fc.run("timeline.trim", clip=cid, edge="out", mode="regular", delta=-extra)
    fc.run("timeline.move", moves=[{"clip": cid, "track": "V3", "time": target * FRAME}], insert=False, linked=False)
    c = clip(cid)
    busy.append((c["startFrame"], c["endFrame"]))
    placed.append(cid)
    print(f"{name:30s} V3 {f2tc(c['startFrame'])}–{f2tc(c['endFrame'])} ({n / FPS:3.1f}s) · \"{line}\"")
if tmp is not None:
    fc.run("sequence.deleteTracks", video=tmp)          # only the temp track: the user keeps an empty V4
json.dump(placed, open(os.path.join(SCRATCH, "pecas", "pecas_v3_ids.json"), "w"))
s = fc.run("sequence.inspect")
v3 = sorted([c for t in s["video"] if t["name"] == "Video 3" for c in t["items"]], key=lambda c: c["start"])
over = [(f2tc(a["startFrame"]), f2tc(b["startFrame"])) for a, b in zip(v3, v3[1:]) if a["endFrame"] > b["startFrame"]]
print(f"V3: {len(v3)} clipes · sobreposições: {over or 'nenhuma'} · trilhas: {[t['name'] for t in s['video']]}")

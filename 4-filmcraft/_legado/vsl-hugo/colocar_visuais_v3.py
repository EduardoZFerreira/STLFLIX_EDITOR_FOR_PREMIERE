"""Place the 8 visual-only B-roll inserts (no audio) on V3, copying reframed block pieces when the source range
is in the B-roll pool; otherwise placing from the bin with a static 9:16 fill crop.
Usage: python colocar_visuais_v3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
S_FILL = 3840 / 1080
# (label, timeline start s, duration s, source file, source start s, crop centre x for bin placement)
INSERTS = [
    ("A1 ímã close", 1.55, 2.45, "Arena 3D - EP7", 106.6, None),
    ("A2 STLIA Joinville", 4.00, 2.50, "Arena 3D - EP7", 11.6, None),
    ("B expositor", 28.70, 2.28, "Arena 3D - EP7", 397.0, None),
    ("C TikTok Shop produto", 97.40, 2.08, "Live TikTok Shop", 57.0, None),
    ("D live", 110.33, 2.81, "Live TikTok Shop", 36.0, None),
    ("E caixa embalada", 533.83, 5.22, "Arena 3D - EP5 - Kit Leão", 22.4, 820),
    ("F Cotrim indo às lojas", 662.12, 4.90, "Arena 3D - EP3", 81.0, None),
    ("G expositor", 722.63, 3.30, "Arena 3D - EP7", 398.4, None),
    ("H live com produto", 797.57, 3.98, "Live TikTok Shop", 43.0, None),
]


def fmt(s):
    return f"{int(s // 60)}:{s % 60:05.2f}"


fc = FC()
seq = fc.run("sequence.inspect")
status = {m["name"]: m["item"] for m in fc.run("media.status")}
hugo_end = max(c["end"] for t in seq["video"] if t["name"] == "Video 1" for c in t["items"] if c["item"] < 1000) / T
pool = [c for t in seq["video"] if t["name"] == "Video 1" for c in t["items"] if c["start"] / T > hugo_end + 1]
tmp = None
for label, t0, dur, src, s_a, cx in INSERTS:
    item = status[src + ".mp4"]
    f_a, n, target = round(s_a * FPS), max(1, round(dur * FPS)), round(t0 * FPS)
    pc = next((c for c in pool if c["item"] == item and c["sourceIn"] / T - 0.05 <= s_a and s_a + dur <= c["sourceOut"] / T + 0.05), None)
    if pc is not None:
        park = max(0, target - (f_a - round(pc["sourceIn"] / FRAME)))
        cid = fc.run("timeline.move", moves=[{"clip": pc["clip"], "track": tmp or "new", "time": park * FRAME}],
                     insert=False, linked=False, copy=True)["copied"][0]
        if tmp is None:
            tmp = next(t["id"] for t in fc.run("sequence.inspect")["video"] if any(c["clip"] == cid for c in t["items"]))
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        if f_a * FRAME - c["sourceIn"]:
            fc.run("timeline.trim", clip=cid, edge="in", mode="regular", delta=f_a * FRAME - c["sourceIn"])
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        if (c["end"] - c["start"]) - n * FRAME:
            fc.run("timeline.trim", clip=cid, edge="out", mode="regular", delta=-((c["end"] - c["start"]) - n * FRAME))
        fc.run("timeline.move", moves=[{"clip": cid, "track": "V3", "time": target * FRAME}], insert=False, linked=False)
        how = "copiado do bloco (com o enquadramento)"
    else:
        cid = fc.run("timeline.place", item=item, track="V3", time=target * FRAME, sourceIn=f_a * FRAME,
                     duration=n * FRAME, insert=False, audio=False)["clips"][0]
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        mi = [e["effect"] for e in c["effects"]].index("motion")
        fc.run("effects.setParam", clip=cid, effect=mi, param="scale", value=round(S_FILL * 100, 3))
        fc.run("effects.setParam", clip=cid, effect=mi, param="position", value=[round(1080 + (960 - cx) * S_FILL, 2), 1920.0])
        how = f"do painel Projeto, recorte 9:16 centrado em x={cx}"
    c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
    print(f"{label:24s} V3 {fmt(c['start'] / T)}–{fmt(c['end'] / T)} ← {src[:22]} {fmt(c['sourceIn'] / T)} · {how}")
if tmp is not None:
    fc.run("sequence.deleteTracks", video="empty")
s = fc.run("sequence.inspect")
v3 = sorted([c for t in s["video"] if t["name"] == "Video 3" for c in t["items"]], key=lambda c: c["start"])
over = [(fmt(a["end"] / T), fmt(b["start"] / T)) for a, b in zip(v3, v3[1:]) if a["endFrame"] > b["startFrame"]]
print(f"V3: {len(v3)} clipes · sobreposições: {over or 'nenhuma'} · trilhas: {[t['name'] for t in s['video']]}")

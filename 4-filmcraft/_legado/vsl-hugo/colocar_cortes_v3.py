"""Place the 15 approved visual-only B-roll cutaways (no audio) on V3, straight from the Project bin.
16:9 sources get a static 9:16 fill crop (cx, optional zoom z and cy); vertical sources are scaled to fill.
Source ranges are [a, b) in seconds, b being the next shot's first frame. Usage: python colocar_cortes_v3.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC, SCRATCH

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
S_FILL = 3840 / 1080
VERT = {"Arena 3D EP 01 - Teaser": 200.0, "Live TikTok Shop": 164.0}
TZ, L, E7, E3, E5, STL = "Arena 3D EP 01 - Teaser", "Live TikTok Shop", "Arena 3D - EP7", "Arena 3D - EP3", "Arena 3D - EP5 - Kit Leão", "Arena 3D - EP2 - STL Seller"
# (label, timeline TC where it starts (24 nominal fps), source, a, b, framing)
CUTS = [
    ("1 logo Arena 3D", "01:54:08", TZ, 62.75, 64.80, None),
    ("2 preparação da live", "02:04:19", L, 15.0, 19.0, None),
    ("3 balões de dúvidas", "05:53:03", TZ, 41.3, 44.0, None),
    ("4 calculadora STL Seller", "07:36:22", STL, 90.0, 95.0, dict(cx=930, z=1.2, cy=520)),
    ("5 pra ver quem VENDE MAIS", "08:20:13", E7, 35.3, 37.04, dict(cx=1000)),
    ("6 Luan/Cotrim/Tales", "08:22:21", TZ, 3.63, 6.63, None),
    ("7 Cotrim na rua", "10:23:10", TZ, 26.99, 29.74, None),
    ("8 Cotrim dirigindo", "10:26:16", E3, 65.5, 68.6, dict(cx=820)),
    ("9 fatura R$ 178,27", "11:18:10", E7, 54.0, 58.3, dict(cx=450, z=1.35, cy=580)),
    ("10 celular vitrine", "12:42:21", L, 1.0, 5.1, None),
    ("11 Tales na live", "13:30:08", L, 29.0, 31.3, None),
    ("12a Luan", "17:46:00", TZ, 7.97, 9.09, None),
    ("12b Cotrim", None, TZ, 9.72, 10.51, None),
    ("12c Tales", None, TZ, 11.34, 12.50, None),
    ("13 ímã na geladeira", "18:27:16", E7, 101.6, 104.0, dict(cx=1100)),
    ("14a Luan (formação)", "18:58:04", E5, 3.5, 5.45, dict(cx=1050)),
    ("14b Cotrim (formação)", "19:01:14", E3, 19.2, 21.2, dict(cx=1180)),
    ("14c Tales (formação)", "19:05:05", E3, 359.5, 361.4, dict(cx=1040)),
    ("15 ímãs na mão", "21:01:12", E7, 104.1, 107.4, dict(cx=1100)),
]


def tc2f(tc):
    m, s, f = map(int, tc.split(":"))
    return (m * 60 + s) * 24 + f


def f2tc(f):
    return f"{f // 1440:02d}:{f // 24 % 60:02d}:{f % 24:02d}"


fc = FC()
status = {m["name"]: m["item"] for m in fc.run("media.status")}
seq = fc.run("sequence.inspect")
v3 = sorted([(c["startFrame"], c["endFrame"]) for t in seq["video"] if t["name"] == "Video 3" for c in t["items"]])
placed, cursor = [], None
for label, tc, src, a, b, fr in CUTS:
    f_a, n = round(a * FPS), round(b * FPS) - round(a * FPS)
    target = tc2f(tc) if tc else cursor
    clash = [(x, y) for x, y in v3 if x < target + n and target < y]
    if clash:
        print(f"{label}: PULADO, sobrepõe V3 {[(f2tc(x), f2tc(y)) for x, y in clash]}")
        continue
    cid = fc.run("timeline.place", item=status[src + ".mp4"], track="V3", time=target * FRAME, sourceIn=f_a * FRAME,
                 duration=n * FRAME, insert=False, audio=False)["clips"][0]
    c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
    mi = [e["effect"] for e in c["effects"]].index("motion")
    if fr is None:
        fc.run("effects.setParam", clip=cid, effect=mi, param="scale", value=VERT[src])
        how = f"vertical {VERT[src]:.0f}%"
    else:
        z, cx, cy = fr.get("z", 1.0), fr["cx"], fr.get("cy", 540)
        S = S_FILL * z
        assert 1080 / S <= cx <= 1920 - 1080 / S and 1920 / S <= cy <= 1080 - 1920 / S + 1e-6, label
        fc.run("effects.setParam", clip=cid, effect=mi, param="scale", value=round(S * 100, 3))
        fc.run("effects.setParam", clip=cid, effect=mi, param="position",
               value=[round(1080 + (960 - cx) * S, 2), round(1920 + (540 - cy) * S, 2)])
        how = f"recorte 9:16 x={cx}" + (f" zoom {z}" if z != 1 else "")
    cursor = target + n
    v3.append((target, target + n))
    placed.append(dict(label=label, clip=cid, start=target, end=target + n))
    print(f"{label:26s} V3 {f2tc(target)}–{f2tc(target + n)} ({n / FPS:3.1f}s) ← {src[:24]} {int(a // 60)}:{a % 60:05.2f} · {how}")
json.dump(placed, open(os.path.join(SCRATCH, "cortes_v3_ids.json"), "w"), indent=1)
s = fc.run("sequence.inspect")
v3 = sorted([c for t in s["video"] if t["name"] == "Video 3" for c in t["items"]], key=lambda c: c["start"])
over = [(f2tc(a["startFrame"]), f2tc(b["startFrame"])) for a, b in zip(v3, v3[1:]) if a["endFrame"] > b["startFrame"]]
print(f"V3: {len(v3)} clipes · sobreposições: {over or 'nenhuma'}")

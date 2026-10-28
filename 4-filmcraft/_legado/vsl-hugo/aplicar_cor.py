"""Apply the C2345 grade (S-Log3/S-Gamut3.Cine LUT + Lumetri Basic) to every V1 clip of the active sequence
and report scopes per clip. Usage: python aplicar_cor.py [item ...]  (default: every V1 clip)"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

LUT = "builtin:slog3-sgamut3cine-to-rec709"
GRADE = {"temperature": -75, "tint": -20, "exposure": 0.9, "contrast": 10,
         "highlights": -10, "blacks": -15, "saturation": 85}
T = 254016000000
FRAME = 10594584000

fc = FC()
seq = fc.run("sequence.inspect")
ITEMS = {int(a) for a in sys.argv[1:]}
clips = [i for t in seq["video"] if t["name"] == "Video 1" for i in t["items"] if not ITEMS or i["item"] in ITEMS]
for c in clips:
    fc.run("lumetri.setInputLut", clip=c["clip"], lut=LUT)
    effects = [e["effect"] for e in next(i for t in fc.run("sequence.inspect")["video"] for i in t["items"] if i["clip"] == c["clip"])["effects"]]
    li = effects.index("lumetri")
    for p, v in GRADE.items():
        fc.run("effects.setParam", clip=c["clip"], effect=li, param=p, value=v)
    mid = (c["startFrame"] + c["endFrame"]) // 2 * FRAME / T
    y = fc.luma(mid)
    print(f"clip {c['clip']:3d} @ {mid:6.1f}s | luma min/med/max {y['y']} | sat {y['sat']}")

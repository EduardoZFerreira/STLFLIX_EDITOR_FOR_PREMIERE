"""Apply grade option B (exposure +0.6, blacks -20) to every V1 clip that has the approved Lumetri grade,
then verify each clip's values and report luma spread."""
import os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
CHANGE = {"exposure": 0.6, "blacks": -20}
EXPECT = {"temperature": -75.0, "tint": -20.0, "exposure": 0.6, "contrast": 10.0, "highlights": -10.0, "blacks": -20.0, "saturation": 85.0}
T, FRAME = 254016000000, 10594584000
fc = FC()
v1 = [i for t in fc.run("sequence.inspect")["video"] if t["name"] == "Video 1" for i in t["items"]]
done, skipped = 0, []
for c in v1:
    names = [e["effect"] for e in c["effects"]]
    if "lumetri" not in names:
        skipped.append(c["clip"]); continue
    li = names.index("lumetri")
    for k, v in CHANGE.items():
        fc.run("effects.setParam", clip=c["clip"], effect=li, param=k, value=v)
    done += 1
# verify
bad, lumas = [], []
v1 = [i for t in fc.run("sequence.inspect")["video"] if t["name"] == "Video 1" for i in t["items"]]
for c in v1:
    lum = next((e for e in c["effects"] if e["effect"] == "lumetri"), None)
    if not lum:
        continue
    vals = {k: float(lum["params"][k]["value"].split("(")[1].rstrip(")")) for k in EXPECT}
    if vals != EXPECT:
        bad.append((c["clip"], vals))
for c in v1[::10]:
    mid = (c["startFrame"] + c["endFrame"]) // 2 * FRAME / T
    lumas.append(fc.luma(mid)["y"][1])
print(f"opção B aplicada em {done} clipes; sem Lumetri: {skipped or 'nenhum'}; valores divergentes: {bad or 'nenhum'}")
print(f"luminância média (amostra de {len(lumas)} clipes): min {min(lumas):.1f} · mediana {st.median(lumas):.1f} · máx {max(lumas):.1f}")

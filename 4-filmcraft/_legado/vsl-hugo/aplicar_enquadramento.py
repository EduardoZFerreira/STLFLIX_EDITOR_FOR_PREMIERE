"""Apply scale 110% + position y 1770 (move up 150 px) to every V1 clip whose Motion is still default;
report clips with custom/keyframed Motion instead of overwriting them."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
SCALE, POS = 110, [1080, 1770]
T = 254016000000
fc = FC()
v1 = [i for t in fc.run("sequence.inspect")["video"] if t["name"] == "Video 1" for i in t["items"]]
done, custom = 0, []
for c in v1:
    names = [e["effect"] for e in c["effects"]]
    mi = names.index("motion")
    p = c["effects"][mi]["params"]
    default = (p["scale"]["value"] == "Float(100.0)" and "1080.0" in p["position"]["value"] and "1920.0" in p["position"]["value"]
               and not p["scale"].get("keyframes") and not p["position"].get("keyframes"))
    if not default:
        custom.append((c["clip"], round(c["start"] / T, 1), p["scale"]["value"], p["position"]["value"]))
        continue
    fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=SCALE)
    fc.run("effects.setParam", clip=c["clip"], effect=mi, param="position", value=POS)
    done += 1
v1 = [i for t in fc.run("sequence.inspect")["video"] if t["name"] == "Video 1" for i in t["items"]]
ok = sum(1 for c in v1 if next(e for e in c["effects"] if e["effect"] == "motion")["params"]["scale"]["value"] == "Float(110.0)")
print(f"aplicado em {done} clipes; conferidos com 110%: {ok}/{len(v1)}; com Motion próprio (não alterados): {custom or 'nenhum'}")

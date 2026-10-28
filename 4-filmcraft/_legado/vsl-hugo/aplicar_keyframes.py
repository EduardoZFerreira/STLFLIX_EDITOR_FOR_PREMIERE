"""Apply the 9:16 reframe plans as Motion keyframes on the 16:9 B-roll clips of the active sequence
(non-destructive: scale + position, hold at framing switches, linear while tracking), plus grouped review markers.
Usage: python aplicar_keyframes.py
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T = 254_016_000_000
FPS = 24000 / 1001
FRAME = 10_594_584_000
S_FILL = 3840 / 1080            # 355.56 %: 1080-high source fills the 3840-high sequence
S_ZOOM = 3840 / 722             # 531.9 %: the 722-high screen window fills it
S_FIT = 2160 / 1920             # 112.5 %: whole 16:9 frame across the width
fc = FC()


def pos(cx, cy, s):
    return [round(1080 + (960 - cx) * s, 2), round(1920 + (540 - cy) * s, 2)]


def keys_for(seg):
    """[(source_time, scale, [x, y], interpolation)] for one plan segment."""
    g, a = seg["geo"], seg["a"]
    if g["mode"] == "crop":
        return [(a, S_FILL, pos(g["x"] + 304, 540, S_FILL), "hold")]
    if g["mode"] == "fit_blur":
        return [(a, S_FIT, pos(960, 540, S_FIT), "hold")]
    if g["mode"] == "track":
        ks = g["keys"]
        return [(a + max(0.0, t), S_FILL, pos(x + 304, 540, S_FILL), "linear" if k < len(ks) - 1 else "hold")
                for k, (t, x) in enumerate(ks)]
    ks = g["keys"] if "keys" in g else [(0.0, g["x"], g["y"])]
    return [(a + max(0.0, t), S_ZOOM, pos(x + 203, y + 361, S_ZOOM), "linear" if k < len(ks) - 1 else "hold")
            for k, (t, x, y) in enumerate(ks)]


def main():
    status = {m["name"]: m["item"] for m in fc.run("media.status")}
    seq = fc.run("sequence.inspect")
    for plan_path in sorted(glob.glob(os.path.join("broll", "an_*_plan.json"))):
        plan = json.load(open(plan_path, encoding="utf-8"))
        name = os.path.basename(plan["src"])
        item = status.get(name)
        clips = [c for t in seq["video"] for c in t["items"] if c["item"] == item]
        n_keys = 0
        for c in clips:
            s_in, s_out = c["sourceIn"] / T, c["sourceOut"] / T
            mi = [e["effect"] for e in c["effects"]].index("motion")
            mp = next(e for e in c["effects"] if e["effect"] == "motion")["params"]
            for p in ("scale", "position"):      # start clean if a previous attempt left keyframes
                if mp[p].get("keyframes"):
                    fc.run("effects.toggleAnimation", clip=c["clip"], effect=mi, param=p)
            ks = [k for seg in plan["segments"] if seg["b"] > s_in and seg["a"] < s_out for k in keys_for(seg)]
            ks = [(max(t, s_in), s, xy, it) for t, s, xy, it in ks if t < s_out]
            last_scale = None
            for t, s, xy, interp in ks:
                tseq = c["start"] + round((t - s_in) * T)
                tseq = min(max(tseq, c["start"]), c["end"] - FRAME)
                media_t = round(t * T)
                if s != last_scale:
                    fc.run("effects.setParam", clip=c["clip"], effect=mi, param="scale", value=round(s * 100, 3),
                           time=tseq, keyframe=True)
                    fc.run("effects.setInterpolation", clip=c["clip"], effect=mi, param="scale", mediaTime=media_t,
                           interpolation="hold")
                    last_scale = s
                fc.run("effects.setParam", clip=c["clip"], effect=mi, param="position", value=xy, time=tseq, keyframe=True)
                fc.run("effects.setInterpolation", clip=c["clip"], effect=mi, param="position", mediaTime=media_t,
                       interpolation=interp)
                n_keys += 1
        # grouped review markers on the media item
        groups = []
        for s in plan["segments"]:
            if not s["why"]:
                continue
            if groups and groups[-1]["why"] == s["why"] and s["a"] - groups[-1]["b"] < 0.5:
                groups[-1]["b"] = s["b"]
            else:
                groups.append({"a": s["a"], "b": s["b"], "why": s["why"]})
        groups = [g for g in groups if g["b"] - g["a"] >= 1.5]
        fc.run("source.open", item=item)
        for g in groups:
            fc.run("markers.add", target="source", time=round(g["a"] * T), durationFrames=max(1, round((g["b"] - g["a"]) * FPS)),
                   name=f"Revisar: {g['why']}", comment="Enquadramento 9:16 automático (keyframes de Movimento).", color="Mango")
        print(f"{name}: {len(clips)} clipe(s), {n_keys} keyframes de posição, {len(groups)} marcador(es) de revisão")


if __name__ == "__main__":
    main()

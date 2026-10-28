"""Replace the remaining letterboxed (112.5 %) framings on B-roll pieces with a full-height fill crop (355.6 %)
centred on the shot's activity, editing the existing keyframes in place (live app). Skips pieces whose live clip
no longer matches the snapshot. Usage: python tirar_faixa_preta.py <snapshot.fcproj>
"""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC

T = 254_016_000_000
S_FILL, S_FIT = 3840 / 1080, 2160 / 1920
val = lambda x: list(x.values())[0] if isinstance(x, dict) else x

snap = json.load(open(sys.argv[1], encoding="utf-8"))["project"]["items"]
seq = snap["14"]["kind"]["Sequence"]
fc = FC()
live = {c["clip"]: c for t in fc.run("sequence.inspect")["video"] for c in t["items"]}

# activity centre per analysed shot (from analisar_broll.py), keyed by source file name
centres = {}
for p in glob.glob(os.path.join("broll", "an_*_plan.json")):
    plan = json.load(open(p, encoding="utf-8"))
    an = json.load(open(p.replace("_plan.json", ".json"), encoding="utf-8"))
    act = np.load(p.replace("_plan.json", "_act.npy")).astype(np.float32)
    times = np.array([s["t"] for s in an["samples"]])
    out = {}
    for s in plan["segments"]:
        if s["geo"]["mode"] != "fit_blur":
            continue
        idx = np.where((times >= s["a"]) & (times < s["b"]))[0]
        g = act[idx].sum(0) if len(idx) else np.zeros((27, 48))
        cx = 960.0
        if g.sum() > 1e-3 and g.max() > 4 * g.mean():
            cx = float((g * (np.arange(48) + 0.5)).sum() / g.sum() / 48 * 1920)
        out[round(s["a"], 2)] = cx
    centres[os.path.basename(plan["src"])] = out

changed = skipped = 0
for t in seq["video_tracks"]:
    for c in t["items"]:
        nm = snap[str(c["item"])]["name"]
        if nm not in centres:
            continue
        lc = live.get(c["id"])
        if lc is None or lc["sourceIn"] != c["source_in"] or lc["start"] != c["start"]:
            skipped += 1
            continue
        s_in, s_out = c["source_in"] / T, (c["source_in"] + c["duration"]) / T
        mo = next(e for e in c["effects"] if e["effect"] == "motion")["params"]
        sk = sorted((k["time"] / T, val(k["value"])) for k in mo["scale"].get("keyframes", []))
        pk = {round(k["time"] / T, 2): k for k in mo["position"].get("keyframes", [])}
        mi = [e["effect"] for e in lc["effects"]].index("motion")
        for i, (tk, sv) in enumerate(sk):
            t_next = sk[i + 1][0] if i + 1 < len(sk) else 1e9
            governs_piece = tk < s_out and t_next > s_in
            if abs(sv - S_FIT * 100) > 0.6 or not governs_piece:
                continue
            cx = centres[nm].get(round(tk, 2), 960.0)
            x = 1080 + (960 - float(np.clip(cx, 304, 1616))) * S_FILL
            fc.run("effects.setKeyframe", clip=c["id"], effect=mi, param="scale", mediaTime=round(tk * T), value=round(S_FILL * 100, 3))
            if round(tk, 2) in pk:
                fc.run("effects.setKeyframe", clip=c["id"], effect=mi, param="position", mediaTime=pk[round(tk, 2)]["time"],
                       value=[round(x, 2), 1920.0])
            changed += 1
            print(f"  {nm[:30]} (pedaço em {int(c['start'] / T // 60)}:{c['start'] / T % 60:05.2f}) trecho de {tk:6.1f}s: 112,5% → 355,6%, centro x={cx:.0f}")
print(f"faixas pretas removidas: {changed} · pedaços pulados por terem mudado desde o snapshot: {skipped}")

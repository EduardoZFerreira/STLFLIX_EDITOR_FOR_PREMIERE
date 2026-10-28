"""Replace the raw 3D-piece takes (IMG_52xx.MOV) in the V1 pool with their reviewed segments (video only),
reframed to 9:16 with Motion keyframes that follow the piece (pecas/an_<name>.json from analisar_pecas.py).
Backs Sequence 01 up first. Usage: python aplicar_pecas.py   (re-running resumes after the last segment already named "Peça · …")
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC, SCRATCH

T, FRAME, FPS = 254_016_000_000, 10_594_584_000, 24000 / 1001
GAP = 12                                   # frames between segments in the pool
LABEL = {"IMG_5228": "narval", "IMG_5229": "narval (2)", "IMG_5230": "ornitorrinco", "IMG_5231": "tubarão-baleia",
         "IMG_5232": "tartaruga verde", "IMG_5233": "tartaruga escura", "IMG_5234": "bonecos (troca)",
         "IMG_5235": "bonecos enfileirados", "IMG_5236": "bonecos e chaveiros", "IMG_5237": "chaveiros",
         "IMG_5238": "tartaruga chaveiro", "IMG_5239": "polvo", "IMG_5242": "boneco grande"}


def f2tc(f):
    return f"{f // 1440:02d}:{f // 24 % 60:02d}:{f % 24:02d}"


fc = FC()
seq = fc.run("sequence.inspect")
status = {m["name"]: m["item"] for m in fc.run("media.status")}
raw = [c for t in seq["video"] + seq["audio"] for c in t["items"] if c["name"].upper().startswith("IMG_52")]
done = {c["name"]: c for t in seq["video"] for c in t["items"] if c["name"].startswith("Peça · ")}
if raw:                                    # first run: back up, then drop the raw takes
    start = min(c["startFrame"] for c in raw)
    fc.run("project.select", items=[seq["id"]])
    fc.run("edit.duplicate")
    print("backup da Sequence 01 criado")
    fc.run("edit.clear", clips=[c["clip"] for c in raw])
    print(f"{len(raw)} clipes brutos removidos (vídeo + áudio)")
    cursor = start
else:                                      # resume after an interruption: continue after the last placed segment
    start = min(c["startFrame"] for c in done.values())
    cursor = max(c["endFrame"] for c in done.values()) + GAP
placed = []
for name in sorted(LABEL):
    an = json.load(open(os.path.join(SCRATCH, "pecas", f"an_{name}.json"), encoding="utf-8"))
    sw = an["src_w"]
    S = 3840 / (sw * 9 / 16)                 # fill the 3840-high sequence
    cxs = sw / 2
    for k, p in enumerate(an["plan"], 1):
        a, b = p["a"], p["b"]
        n = round((b - a) * FPS)
        nm = f"Peça · {LABEL[name]}" + (f" {k}" if len(an["plan"]) > 1 else "")
        if nm in done:
            d = done[nm]
            placed.append(dict(name=name, clip=d["clip"], start=d["startFrame"], end=d["endFrame"], a=a, b=b))
            continue
        cid = fc.run("timeline.place", item=status[name + ".MOV"], track="V1", time=cursor * FRAME,
                     sourceIn=round(a * T), duration=n * FRAME, insert=False, audio=False)["clips"][0]
        c = next(c for t in fc.run("sequence.inspect")["video"] for c in t["items"] if c["clip"] == cid)
        mi = [e["effect"] for e in c["effects"]].index("motion")
        fc.run("effects.setParam", clip=cid, effect=mi, param="scale", value=round(S * 100, 3))
        keys = p["keys"]
        pos = lambda cx: [round(1080 + (cxs - cx) * S, 2), 1920.0]
        if len(keys) == 1:
            fc.run("effects.setParam", clip=cid, effect=mi, param="position", value=pos(keys[0][1]))
        else:
            for t, cx in keys:
                tseq = c["start"] + round((t - a) * T)
                tseq = min(max(tseq, c["start"]), c["end"] - FRAME)
                fc.run("effects.setParam", clip=cid, effect=mi, param="position", value=pos(cx), time=tseq, keyframe=True)
                fc.run("effects.setInterpolation", clip=cid, effect=mi, param="position",
                       mediaTime=c["sourceIn"] + (tseq - c["start"]),
                       interpolation="linear")
        fc.run("clip.rename", clip=cid, name=nm)
        placed.append(dict(name=name, clip=cid, start=cursor, end=cursor + n, a=a, b=b, keys=len(keys)))
        print(f"{nm:28s} V1 {f2tc(cursor)}–{f2tc(cursor + n)} ({n / FPS:4.1f}s) ← {name} {a:5.1f}–{b:5.1f}s · {len(keys)} keyframe(s)")
        cursor += n + GAP
json.dump(placed, open(os.path.join(SCRATCH, "pecas", "pecas_ids.json"), "w"), indent=1)
print(f"{len(placed)} trechos de {f2tc(start)} a {f2tc(cursor - GAP)}")

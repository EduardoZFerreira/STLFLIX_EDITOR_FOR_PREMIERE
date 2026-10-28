"""Save a compact snapshot of the active sequence (clips, transitions, markers, non-default effect params)
and print it. Usage: python snapshot.py <out.json>"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
T, FPS = 254_016_000_000, 24000 / 1001

def tc(ticks):
    s = ticks / T
    return f"{int(s // 60)}:{s % 60:05.2f}"

s = FC().run("sequence.inspect")
snap = {"durationFrames": s.get("durationFrames"), "tracks": {}, "markers": []}
for kind in ("video", "audio"):
    for t in s[kind]:
        items = []
        for i in t["items"]:
            eff = {}
            for e in i["effects"]:
                ch = {k: v["value"] for k, v in e["params"].items() if v.get("keyframes")} if False else None
                eff[e["effect"]] = {k: v["value"] for k, v in e["params"].items()} | ({"_kf": sum(v.get("keyframes", 0) for v in e["params"].values())})
            items.append({"clip": i["clip"], "name": i["name"], "start": i["start"], "end": i["end"],
                          "sourceIn": i["sourceIn"], "sourceOut": i["sourceOut"], "speed": i.get("speed"),
                          "gainDb": i.get("gainDb"), "enabled": i.get("enabled"), "effects": eff})
        snap["tracks"][t["name"]] = {"items": items, "transitions": [
            {k: tr[k] for k in ("id", "effect", "from", "to", "start", "duration", "align")} for tr in t.get("transitions", [])],
            "muted": t.get("muted"), "volume_db": t.get("volume_db")}
snap["markers"] = [{k: m.get(k) for k in ("id", "name", "start", "duration", "color", "comment")} for m in s.get("markers", [])]
json.dump(snap, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=0)
for name, t in snap["tracks"].items():
    if t["items"] or t["transitions"]:
        print(f"== {name}: {len(t['items'])} clipes, {len(t['transitions'])} transições")
print("markers:", len(snap["markers"]), "| duração:", snap["durationFrames"], "frames")

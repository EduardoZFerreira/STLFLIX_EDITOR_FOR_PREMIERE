"""Render a few Program frames through the export path (file.exportFrame, originals) and report mean luma,
to tell whether G: originals decode. Usage: python teste_render.py tag"""
import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC, SCRATCH
T = 254016000000
fc = FC()
s = fc.run("sequence.inspect")
v1 = sorted([c for t in s["video"] if t["name"] == "Video 1" for c in t["items"] if c["end"] <= s["out"]], key=lambda c: c["start"])
pick = {}
for c in v1:
    pick.setdefault(c["name"], c)
v3 = [c for t in s["video"] if t["name"] == "Video 3" for c in t["items"] if c["end"] <= s["out"]]
for c in v3[:3]:
    pick.setdefault("V3 " + c["name"], c)
os.makedirs(os.path.join(SCRATCH, "teste_render"), exist_ok=True)
for name, c in pick.items():
    p = os.path.join(SCRATCH, "teste_render", f"{sys.argv[1]}_{len(name)}_{c['clip']}.png")
    fc.run("file.exportFrame", path=p, format="png", target="program", time=(c["start"] + c["end"]) // 2)
    y = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "scale=54:96,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    print(f"{name[:34]:34s} luma média {sum(y) / max(1, len(y)):5.1f}")

"""Rebuild the audio of "TAKES EXTRAS · VERSÕES CURTAS" that the FCP7 XML import dropped.

In the XML every audio clipitem that touches a cross-fade has start/end = -1 (position implied by the transition),
and FilmCraft skipped those: only 6 of 81 clips per track came in. Here each audio cut is placed on the same span
and source range as its video clip (cut-only, from the XML video track), A1 panned -100 / A2 +100 like the rest of
the project, then the XML's 6-frame centred Cross Fade (+3 dB) = Constant Power is re-applied on every cut that
had one. The sequence is duplicated first (backup). Usage: python reconstruir_extras.py <xml> <sequence id>
"""
import os, sys, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fc import FC

T, FRAME = 254_016_000_000, 10_594_584_000
XML, SEQ = sys.argv[1], int(sys.argv[2])
NAME = "TAKES EXTRAS · VERSÕES CURTAS"

root = ET.parse(XML).getroot()
s = next(x for x in root.iter("sequence") if x.findtext("name") == NAME)
vids = [(int(c.findtext("start")), int(c.findtext("end")), int(c.findtext("in")), c.findtext("name"))
        for c in s.find("media/video").findall("track")[0].findall("clipitem")]
# cuts that carry an audio cross-fade in the XML (transition centred between two audio clips)
atr = s.find("media/audio").findall("track")[0]
fades = []
for el in atr:
    if el.tag == "transitionitem":
        fades.append((int(el.findtext("start")) + int(el.findtext("end"))) // 2)
fade_frames = {int(el.findtext("end")) - int(el.findtext("start")) for el in atr if el.tag == "transitionitem"}

fc = FC()
seq = fc.run("sequence.inspect", item=SEQ)
assert seq["name"] == NAME, seq["name"]
items = {c["name"]: c["item"] for c in seq["video"][0]["items"]}           # same media items as the video
fc.run("project.select", items=[SEQ])
fc.run("edit.duplicate")
print("backup da sequência criado")
fc.run("sequence.open", item=SEQ)
old = [c["clip"] for t in seq["audio"] for c in t["items"]]
if old:
    fc.run("edit.clear", clips=old)
placed = {"A1": [], "A2": []}
for st, en, src_in, name in vids:
    for tr in ("A1", "A2"):
        r = fc.run("timeline.place", item=items[name], track=tr, time=st * FRAME, sourceIn=src_in * FRAME,
                   duration=(en - st) * FRAME, insert=False, video=False)
        placed[tr] += [(st, en, cid) for cid in r["clips"]]
seq = fc.run("sequence.inspect", item=SEQ)
by = {c["clip"]: c for t in seq["audio"] for c in t["items"]}
for tr, bal in (("A1", -100.0), ("A2", 100.0)):
    for st, en, cid in placed[tr]:
        c = by[cid]
        idx = [e["effect"] for e in c["effects"]]
        if "panner" in idx:
            fc.run("effects.setParam", clip=cid, effect=idx.index("panner"), param="balance", value=bal)
n_fx = 0
ff = max(fade_frames) if fade_frames else 6
for tr in ("A1", "A2"):
    for st, en, cid in placed[tr]:
        if en in fades:
            fc.run("sequence.applyAudioTransition", clip=cid, effect="constant_power", frames=ff, edge="out")
            n_fx += 1
seq = fc.run("sequence.inspect", item=SEQ)
cov = {t["name"]: round(sum(c["end"] - c["start"] for c in t["items"]) / T, 1) for t in seq["audio"] if t["items"]}
print(f"{len(vids)} cortes · áudio por trilha {cov} s · {n_fx} crossfades de {ff} quadros")

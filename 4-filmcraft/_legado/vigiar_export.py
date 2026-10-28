"""Watch a running export job: progress every minute, and every 5 min render one camera-take frame and one
G: B-roll frame through the export path (file.exportFrame); stop with an ALERT as soon as they come out black
(G: originals unreadable). At the end, scan the output every 5 s for black stretches.
Usage: python vigiar_export.py <job id> <output.mp4>"""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC, SCRATCH

job, out = int(sys.argv[1]), sys.argv[2]
fc = FC()
s = fc.run("sequence.inspect")
st = {m["item"]: m for m in fc.run("media.status")}
probes = []
for name in ("Video 1", "Video 3"):
    cl = sorted([c for t in s["video"] if t["name"] == name for c in t["items"]
                 if c["end"] <= s["out"] and st.get(c["item"], {}).get("path", "").upper().startswith("G:")],
                key=lambda c: c["end"] - c["start"], reverse=True)
    if cl:
        probes.append((f"{name}: {cl[0]['name'][:28]}", (cl[0]["start"] + cl[0]["end"]) // 2))


def health():
    res = []
    for k, (lab, t) in enumerate(probes):
        p = os.path.join(SCRATCH, "teste_render", f"vigia_{k}.png")
        fc.run("file.exportFrame", path=p, format="png", target="program", time=t)
        y = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "scale=54:96,format=gray", "-f", "rawvideo", "-"],
                           capture_output=True).stdout
        res.append((lab, sum(y) / max(1, len(y))))
    return res


last_h, last = 0, None
while True:
    try:
        j = next(j for j in fc.run("jobs.list") if j["id"] == job)
    except Exception as e:
        print(time.strftime("%H:%M"), "poll falhou:", str(e)[:100], flush=True); time.sleep(60); fc = FC(); continue
    msg = f"{time.strftime('%H:%M')} {100 * (j.get('progress') or 0):4.1f}% ({j.get('done')}/{j.get('total')}) eta {int((j.get('etaSeconds') or 0) / 60)} min"
    if j.get("finished"):
        print(msg, "|", j["status"], "| offlineMedia:", j.get("offlineMedia"), flush=True)
        break
    if time.time() - last_h > 300:
        h = health()
        last_h = time.time()
        print(msg, "| leitura G:", " · ".join(f"{l} {v:.0f}" for l, v in h), flush=True)
        if any(v < 30 for _, v in h):
            print("ALERTA: mídia do G: renderizando preta — a exportação está saindo com tela preta", flush=True)
            sys.exit(2)
    time.sleep(60)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-vf", "fps=1/5,scale=54:96,format=gray", "-f", "rawvideo", "-"],
                     capture_output=True).stdout
n = 54 * 96
lum = [sum(raw[i:i + n]) / n for i in range(0, len(raw), n)]
dark = [i * 5 for i, v in enumerate(lum) if v < 4]
print(f"{len(lum)} amostras, {len(dark)} pretas:", " ".join(f"{t // 60}:{t % 60:02d}" for t in dark[:80]), flush=True)

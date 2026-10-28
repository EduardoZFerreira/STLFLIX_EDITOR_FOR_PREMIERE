"""Poll an export job until it finishes, then sample the output every 5 s and list black stretches.
Usage: python acompanhar_export.py <job id> <output.mp4>"""
import os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fc import FC
job, out = int(sys.argv[1]), sys.argv[2]
last = None
while True:
    try:
        j = next(j for j in FC().run("jobs.list") if j["id"] == job)
    except Exception as e:
        print("poll falhou:", str(e)[:120], flush=True); time.sleep(30); continue
    msg = f"{time.strftime('%H:%M')} {j['status'][:50]} {100 * (j.get('progress') or 0):.0f}% eta {j.get('etaSeconds')}"
    if msg != last:
        print(msg, flush=True); last = msg
    if j.get("finished"):
        print("offlineMedia:", j.get("offlineMedia"), "result:", str(j.get("result"))[:300], flush=True)
        break
    time.sleep(30)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-vf", "fps=1/5,scale=54:96,format=gray", "-f", "rawvideo", "-"],
                     capture_output=True).stdout
n = 54 * 96
lum = [sum(raw[i:i + n]) / n for i in range(0, len(raw), n)]
dark = [i * 5 for i, v in enumerate(lum) if v < 4]
print(f"{len(lum)} amostras, {len(dark)} pretas:", " ".join(f"{t // 60}:{t % 60:02d}" for t in dark[:60]), flush=True)

"""Rebuild the dialogue (A1, timeline order) of a FilmCraft sequence (by id) as a 16 kHz mono WAV + clip map.
Usage: python corpo_audio.py <sequence id> <out.wav> <out_clips.json>"""
import json, os, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fc import FC
T, SR = 254_016_000_000, 16000
fc = FC()
paths = {m["item"]: m["path"] for m in fc.run("media.status")}
s = fc.run("sequence.inspect", item=int(sys.argv[1]))
a1 = sorted((c for c in s["audio"][0]["items"] if c["enabled"]), key=lambda c: c["start"])
end = max(c["end"] for c in a1) / T
buf = np.zeros(int(end * SR) + SR, np.int16)
clips = []
for k, c in enumerate(a1):
    s0, dur = c["sourceIn"] / T, (c["end"] - c["start"]) / T
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s0:.4f}", "-t", f"{dur:.4f}", "-i", paths[c["item"]], "-vn",
                          "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
    pcm = np.frombuffer(raw, np.int16)
    i0 = int(round(c["start"] / T * SR))
    buf[i0:i0 + len(pcm)] = pcm[:len(buf) - i0]
    clips.append(dict(start=round(c["start"] / T, 3), dur=round(dur, 3), take=c["name"], src_in=round(s0, 3)))
    if k % 100 == 0:
        print(k, "/", len(a1), flush=True)
with wave.open(sys.argv[2], "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(buf[:int(end * SR)].tobytes())
json.dump(dict(sequence=s["name"], duration=end, clips=clips), open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
print(f"{s['name']}: {end / 60:.1f} min, {len(clips)} clipes")

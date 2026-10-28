"""Rebuild each 'Lead X' sequence's dialogue audio of VSL-Shark (A1 clips, timeline order, gaps as silence)
as 16 kHz mono WAVs, from a COPY of the project file (read only), plus a JSON map of the clips used.
Usage: python leads_audio.py <project copy.fcproj>
"""
import json, os, subprocess, sys
import numpy as np

T, SR = 254_016_000_000, 16000
HERE = os.path.dirname(os.path.abspath(__file__))
p = json.load(open(sys.argv[1], encoding="utf-8"))
items = p["project"]["items"]


def media_path(item):
    m = items[str(item)]["kind"]["Media"]["media"]
    return next(iter(m.values()))["path"]


leads = sorted((it["name"], k) for k, it in items.items()
               if "Sequence" in it.get("kind", {}) and it["name"].startswith("Lead "))
info = {}
for name, k in leads:
    sq = items[k]["kind"]["Sequence"]
    a1 = sorted(sq["audio_tracks"][0]["items"], key=lambda c: c["start"])
    end = max(c["start"] + c["duration"] for c in a1) / T
    buf = np.zeros(int(end * SR) + SR, np.int16)
    clips = []
    for c in a1:
        if not c.get("enabled", True):
            continue
        src, s0, dur = media_path(c["item"]), c["source_in"] / T, c["duration"] / T
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{s0:.4f}", "-t", f"{dur:.4f}", "-i", src, "-vn",
                              "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True).stdout
        pcm = np.frombuffer(raw, np.int16)
        i0 = int(round(c["start"] / T * SR))
        buf[i0:i0 + len(pcm)] = pcm[:len(buf) - i0]
        clips.append(dict(start=round(c["start"] / T, 3), dur=round(dur, 3), take=c["name"], src_in=round(s0, 3)))
    wav = os.path.join(HERE, f"{name.replace(' ', '_')}.wav")
    import wave
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(buf[:int(end * SR)].tobytes())
    markers = [dict(t=round(m.get("start", 0) / T, 2), name=m.get("name", ""), comment=m.get("comment", ""))
               for m in sq.get("markers", [])]
    info[name] = dict(seq=k, duration=round(end, 2), clips=clips, markers=markers, wav=wav)
    print(f"{name}: {end:5.1f}s, {len(clips)} clipes, takes {sorted({c['take'] for c in clips})}")
json.dump(info, open(os.path.join(HERE, "leads.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

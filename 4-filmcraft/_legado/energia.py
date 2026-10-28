"""Print speech islands (RMS above threshold, 50 ms hops) inside given ranges of a 16 kHz mono WAV.
Usage: python energia.py file.wav a-b [a-b ...]"""
import sys, wave
import numpy as np
with wave.open(sys.argv[1], "rb") as w:
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
hop = 800
rms = np.sqrt(np.convolve(x * x, np.ones(hop) / hop, mode="same"))[::hop]
db = 20 * np.log10(rms + 1e-9)
floor = np.percentile(db, 10)
thr = floor + 18
print(f"ruído {floor:.1f} dB, limiar {thr:.1f} dB")
for r in sys.argv[2:]:
    a, b = map(float, r.split("-"))
    seg = db[int(a * 20):int(b * 20)]
    on = seg > thr
    islands, start = [], None
    for i, v in enumerate(np.append(on, False)):
        t = a + i / 20
        if v and start is None: start = t
        if not v and start is not None:
            if t - start >= 0.1: islands.append(f"{start:.2f}-{t:.2f}")
            start = None
    # merge gaps < 0.25 s
    print(f"{r}: " + ", ".join(islands))

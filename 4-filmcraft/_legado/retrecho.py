"""Re-transcribe short ranges of a 16 kHz mono WAV in isolation (word timestamps, absolute times).
Usage: python retrecho.py file.wav a-b [a-b ...]"""
import glob, os, sys, wave
for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
    os.add_dll_directory(d); os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]
import numpy as np
from faster_whisper import WhisperModel
with wave.open(sys.argv[1], "rb") as w:
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
m = WhisperModel("large-v3-turbo", device="cuda", compute_type="float16")
for r in sys.argv[2:]:
    a, b = map(float, r.split("-"))
    segs, _ = m.transcribe(x[int(a * 16000):int(b * 16000)], language="pt", word_timestamps=True,
                           condition_on_previous_text=False, temperature=0)
    ws = [f"{w.word.strip()}[{a + w.start:.2f}-{a + w.end:.2f}]" for s in segs for w in (s.words or [])]
    print(f"--- {r}: " + " ".join(ws), flush=True)

"""Transcribe a WAV with faster-whisper (word timestamps) -> JSON {language, words:[{text,start,end}], segments:[...]}.

Usage: python transcribe.py <in.wav> <out.json> [model]
"""
import glob
import json
import os
import sys
import time

# Make the pip-installed CUDA DLLs (cuBLAS / cuDNN) findable on Windows.
for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
    os.add_dll_directory(d)
    os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]

from faster_whisper import WhisperModel  # noqa: E402

wav, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"

try:
    model = WhisperModel(model_name, device="cuda", compute_type="float16")
    device = "cuda"
except Exception as e:  # no usable GPU runtime: fall back to CPU
    print(f"GPU indisponível ({e}); usando CPU", file=sys.stderr)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    device = "cpu"

import wave  # noqa: E402

import numpy as np  # noqa: E402

# Expects 16 kHz mono s16 (ffmpeg -ac 1 -ar 16000); decoded here to avoid PyAV version issues.
with wave.open(wav, "rb") as w:
    if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
        sys.exit("WAV precisa ser 16 kHz mono 16-bit")
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0

t0 = time.time()
segments, info = model.transcribe(
    audio,
    language="pt",
    word_timestamps=True,
    vad_filter=False,
    condition_on_previous_text=False,
    initial_prompt=("Impressão 3D, STLFLIX, STLIA, STLSeller, STLAcademy, Joinville, TikTok Shop, Shopee, Arena 3D, "
                    "Higor, Tales, Hugo, Cotrim, Luan, Lincoln, Uniquebox, Petare, Michelle, Adriano, Emerson, Ana, "
                    "Elite 3D, Black November, vitalício, Fusion."),
)
words, segs = [], []
for s in segments:
    segs.append({"start": s.start, "end": s.end, "text": s.text.strip()})
    for w in s.words or []:
        words.append({"text": w.word.strip(), "start": w.start, "end": w.end, "p": round(w.probability, 3)})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text.strip()}", flush=True)

with open(out, "w", encoding="utf-8") as f:
    json.dump({"language": "pt", "model": model_name, "device": device, "duration": info.duration,
               "segments": segs, "words": words}, f, ensure_ascii=False, indent=1)
print(f"OK {len(words)} palavras, {len(segs)} segmentos em {time.time() - t0:.1f}s ({device})", file=sys.stderr)

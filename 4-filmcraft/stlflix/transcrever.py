"""Transcrição com faster-whisper (timestamps por palavra) → {language, model, duration, segments, words}."""
import glob
import json
import os
import sys
import time
import wave

import numpy as np


def _dlls_cuda():
    # torna as DLLs CUDA instaladas pelo pip (cuBLAS / cuDNN) visíveis no Windows
    for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
        os.add_dll_directory(d)
        os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


def transcrever(wav_16k, saida_json, modelo="large-v3-turbo", idioma="pt", nomes=()):
    _dlls_cuda()
    from faster_whisper import WhisperModel
    try:
        m = WhisperModel(modelo, device="cuda", compute_type="float16")
        dev = "cuda"
    except Exception as e:                      # sem GPU: funciona, só que mais devagar
        print(f"GPU indisponível ({e}); usando CPU", file=sys.stderr)
        m = WhisperModel(modelo, device="cpu", compute_type="int8")
        dev = "cpu"
    with wave.open(wav_16k, "rb") as w:
        if w.getframerate() != 16000 or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError("o WAV precisa ser 16 kHz mono 16-bit")
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    t0 = time.time()
    prompt = ", ".join(nomes) + "." if nomes else None
    segs, info = m.transcribe(audio, language=idioma, word_timestamps=True, vad_filter=False,
                              condition_on_previous_text=False, initial_prompt=prompt)
    out_s, out_w = [], []
    for s in segs:
        out_s.append({"start": s.start, "end": s.end, "text": s.text.strip()})
        for w in s.words or []:
            out_w.append({"text": w.word.strip(), "start": w.start, "end": w.end, "p": round(w.probability, 3)})
    json.dump({"language": idioma, "model": modelo, "device": dev, "duration": info.duration,
               "segments": out_s, "words": out_w}, open(saida_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return dict(palavras=len(out_w), segmentos=len(out_s), segundos=round(time.time() - t0, 1), device=dev)


def suspeitas(tr, max_palavra_s=0.8):
    """Palavras esticadas: o Whisper costuma fundir frases repetidas (tropeços) numa palavra longa."""
    return [(w["start"], w["text"]) for w in tr["words"] if w["end"] - w["start"] > max_palavra_s]

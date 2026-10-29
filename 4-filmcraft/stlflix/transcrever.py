"""Transcrição com faster-whisper (timestamps por palavra) → {language, model, duration, segments, words}."""
import glob
import json
import os
import sys
import time
import wave

import numpy as np

# o download do modelo avisa (em inglês) que o Windows não deixa criar atalhos no cache: inofensivo, só assusta o editor
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def _dlls_cuda():
    # torna as DLLs CUDA instaladas pelo pip (cuBLAS / cuDNN) visíveis no Windows
    for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
        os.add_dll_directory(d)
        os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


def modelo_baixado(modelo="large-v3-turbo"):
    """O modelo do Whisper já está no cache deste computador (~/.cache/huggingface)?"""
    from faster_whisper.utils import download_model
    try:
        download_model(modelo, local_files_only=True)
        return True
    except Exception:                           # noqa: BLE001 — qualquer falha aqui quer dizer "não está"
        return False


def garantir_modelo(modelo="large-v3-turbo"):
    """Baixa o modelo na primeira vez (o large-v3-turbo tem ~1,6 GB); depois ele fica no cache do computador."""
    if not modelo_baixado(modelo):
        print(f"baixando o modelo do Whisper '{modelo}' (só na primeira vez; o large-v3-turbo tem ~1,6 GB)…", file=sys.stderr)
        from faster_whisper.utils import download_model
        download_model(modelo)


_CARREGADOS = {}                                # modelo já carregado, para transcrever vários brutos sem recarregar


def _carregar(modelo):
    if modelo not in _CARREGADOS:
        _dlls_cuda()
        garantir_modelo(modelo)
        from faster_whisper import WhisperModel
        try:
            _CARREGADOS[modelo] = (WhisperModel(modelo, device="cuda", compute_type="float16"), "cuda")
        except Exception as e:                  # sem GPU: funciona, só que mais devagar
            print(f"GPU indisponível ({e}); usando CPU", file=sys.stderr)
            _CARREGADOS[modelo] = (WhisperModel(modelo, device="cpu", compute_type="int8"), "cpu")
    return _CARREGADOS[modelo]


def transcrever(wav_16k, saida_json, modelo="large-v3-turbo", idioma="pt", nomes=()):
    m, dev = _carregar(modelo)
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

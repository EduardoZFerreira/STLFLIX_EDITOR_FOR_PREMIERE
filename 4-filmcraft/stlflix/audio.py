"""Áudio de uma sequência para transcrever.

O caminho seguro é exportar a mixagem pelo próprio FilmCraft: inclui sequências aninhadas, ganho e pan, e mostra
o que o espectador vai ouvir (inclusive trechos mudos por erro de montagem ou de importação de XML).
"""
import os
import subprocess
import wave

from .tempo import T


def exportar_mix(fc, seq_id, destino_wav_16k):
    """Exporta a sequência inteira em WAV pelo FilmCraft e converte para 16 kHz mono (formato do Whisper)."""
    bruto = destino_wav_16k.replace(".wav", "_mix.wav")
    if os.path.exists(bruto):
        os.remove(bruto)
    fc.run("file.exportMedia", path=bruto, format="wav", sequence=seq_id, range="entire", wait=False)
    job = fc.esperar_job(os.path.basename(bruto))
    if not os.path.exists(bruto):
        raise RuntimeError(f"exportação do áudio falhou: {job.get('status')}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", bruto, "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
                    destino_wav_16k], check=True)
    return bruto


def trechos_mudos(wav_16k, limiar_db=-60.0, minimo_s=3.0):
    """[(início, fim)] em segundos de trechos sem som (ex.: áudio que não veio na importação do XML)."""
    import numpy as np
    with wave.open(wav_16k, "rb") as w:
        sr = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    janela = sr // 2
    n = len(a) // janela
    rms = np.sqrt((a[:n * janela].reshape(n, janela) ** 2).mean(axis=1) + 1e-12)
    mudo = 20 * np.log10(rms) < limiar_db
    out, i = [], 0
    while i < n:
        if mudo[i]:
            j = i
            while j < n and mudo[j]:
                j += 1
            if (j - i) * 0.5 >= minimo_s:
                out.append((i * 0.5, j * 0.5))
            i = j
        else:
            i += 1
    return out


def mapa_de_cortes(seq):
    """Cortes da sequência na ordem da timeline: início, duração, take e tempo no bruto (para anotar a transcrição).
    Sequências aninhadas entram pelo nome da sequência."""
    v1 = sorted((c for c in seq["video"][0]["items"] if c["enabled"]), key=lambda c: c["start"])
    a1 = sorted((c for c in seq["audio"][0]["items"] if c["enabled"]), key=lambda c: c["start"]) if seq["audio"] else []
    base = a1 or v1
    cortes = [dict(start=c["start"] / T, dur=(c["end"] - c["start"]) / T, take=c["name"], src_in=c["sourceIn"] / T)
              for c in base]
    vistos = {round(c["start"], 2) for c in cortes}
    for c in v1:                               # trechos que só existem no vídeo (ex.: sequência aninhada sem áudio)
        if round(c["start"] / T, 2) not in vistos and not any(x["start"] <= c["start"] / T < x["start"] + x["dur"] for x in cortes):
            cortes.append(dict(start=c["start"] / T, dur=(c["end"] - c["start"]) / T, take=c["name"], src_in=c["sourceIn"] / T))
    cortes.sort(key=lambda c: c["start"])
    fim = max((c["end"] for c in seq["video"][0]["items"]), default=0) / T
    return dict(sequencia=seq["name"], duracao=fim, cortes=cortes)


def origem(mapa, t):
    """(take, tempo no bruto) do instante t da sequência."""
    c = next((c for c in mapa["cortes"] if c["start"] - 0.05 <= t < c["start"] + c["dur"]), mapa["cortes"][-1])
    return c["take"].rsplit(".", 1)[0], c["src_in"] + max(0.0, t - c["start"])

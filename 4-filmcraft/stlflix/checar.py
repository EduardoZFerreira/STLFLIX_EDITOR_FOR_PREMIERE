"""Checagens antes de exportar: os problemas que já estragaram exportações e revisões.

1. Mídia do Drive ilegível → quadros renderizados pretos (luma ~0) mesmo com o monitor normal.
2. Trilha de vídeo com clipes, mas desligada (o "olho" apagado) → motions não aparecem.
3. Áudio só de um lado: todos os clipes com pan −100 numa trilha só.
4. Áudio dobrado: sequência aninhada com pan 0 em duas trilhas (+5 a 6 dB).
5. Áudio que não veio na importação de XML: vídeo coberto por muito mais tempo que o áudio.
"""
import os
import subprocess
import tempfile

from .tempo import T, mmss


def _balance(c):
    p = next((e for e in c["effects"] if e["effect"] == "panner"), None)
    return float(p["params"]["balance"]["value"].strip("Float()")) if p else None


def _cobertura(itens):
    return sum(c["end"] - c["start"] for c in itens) / T


def _luma(fc, seq_id, t_ticks):
    p = os.path.join(tempfile.gettempdir(), f"stlflix_check_{seq_id}_{t_ticks}.png")
    fc.run("file.exportFrame", path=p, format="png", target="program", time=t_ticks, sequence=seq_id)
    y = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-vf", "scale=54:96,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True).stdout
    os.remove(p)
    return sum(y) / max(1, len(y))


def checar(fc, nomes_seq, testar_render=True):
    """[(gravidade, sequência, mensagem)] — gravidade: ERRO (estraga a exportação) ou AVISO."""
    seqs = fc.sequencias()
    status = {m["item"]: m for m in fc.run("media.status")}
    achados = []
    for nome in nomes_seq:
        if nome not in seqs:
            achados.append(("ERRO", nome, "sequência não existe no projeto"))
            continue
        s = fc.run("sequence.inspect", item=seqs[nome])
        for t in s["video"]:
            if t["items"] and not t["enabled"]:
                achados.append(("ERRO", nome, f"{t['name']} tem {len(t['items'])} clipes mas está desligada (olho apagado)"))
        audio = [t for t in s["audio"] if t["items"]]
        cob_v = _cobertura(s["video"][0]["items"]) if s["video"] else 0
        if audio:
            cob_a = max(_cobertura(t["items"]) for t in audio)
            if cob_v and cob_a < 0.8 * cob_v:
                achados.append(("ERRO", nome, f"áudio cobre {cob_a:.0f}s de {cob_v:.0f}s de vídeo — faltam cortes de áudio "
                                              "(importação de XML?)"))
            if len(audio) == 1 and all((_balance(c) or 0) <= -99 for c in audio[0]["items"]):
                achados.append(("ERRO", nome, "áudio só do lado esquerdo: todos os clipes com pan −100 e uma trilha só"))
            if len(audio) == 1 and all((_balance(c) or 0) >= 99 for c in audio[0]["items"]):
                achados.append(("ERRO", nome, "áudio só do lado direito: todos os clipes com pan +100 e uma trilha só"))
            aninhados = [c for t in audio for c in t["items"] if c["item"] in seqs.values()]
            if len(audio) >= 2 and any((_balance(c) or 0) == 0 for c in aninhados):
                achados.append(("AVISO", nome, "sequência aninhada com pan 0 nas duas trilhas de áudio: som dobrado "
                                               "(use −100 na A1 e +100 na A2)"))
        elif cob_v:
            achados.append(("ERRO", nome, "sequência sem nenhum clipe de áudio"))
        offline = sorted({status[c["item"]]["name"] for t in s["video"] + s["audio"] for c in t["items"]
                          if c["item"] in status and status[c["item"]].get("status") != "online"})
        if offline:
            achados.append(("ERRO", nome, f"mídia offline: {', '.join(offline[:6])}"))
        if testar_render and s["video"] and s["video"][0]["items"]:
            amostra = {}
            for c in s["video"][0]["items"]:              # 1 quadro por arquivo do Drive
                p = (status.get(c["item"]) or {}).get("path") or ""
                if p.upper().startswith("G:") and p not in amostra:
                    amostra[p] = c
            for p, c in list(amostra.items())[:6]:
                meio = (c["start"] + c["end"]) // 2
                if _luma(fc, seqs[nome], meio) < 4:
                    achados.append(("ERRO", nome, f"quadro preto em {mmss(meio / T)} ({os.path.basename(p)}): mídia do "
                                                  "Drive ilegível — rode `reconectar`"))
    return achados

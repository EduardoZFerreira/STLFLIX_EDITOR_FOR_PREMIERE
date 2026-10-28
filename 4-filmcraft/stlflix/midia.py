"""Reconexão de mídia. Arquivos no Google Drive (G:) às vezes ficam ilegíveis para o FilmCraft ("MEDIA UNREADABLE"),
mesmo aparecendo como online; o monitor engana porque toca os proxies, mas a exportação sai PRETA sem aviso.
Reconectar no mesmo caminho resolve."""
import os


def reconectar(fc, prefixo_caminho="G:"):
    feitos, erros = [], []
    for m in fc.run("media.status"):
        p = m.get("path") or ""
        if p.upper().startswith(prefixo_caminho.upper()):
            try:
                fc.run("media.relink", item=m["item"], path=os.path.normpath(p))
                feitos.append(m["name"])
            except Exception as e:                  # noqa: BLE001 — segue com os outros e relata
                erros.append((m["name"], str(e)[:120]))
    return feitos, erros

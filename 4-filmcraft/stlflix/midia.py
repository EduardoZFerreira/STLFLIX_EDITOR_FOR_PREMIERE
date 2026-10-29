"""Reconexão de mídia. Arquivos no Google Drive às vezes ficam ilegíveis para o FilmCraft ("MEDIA UNREADABLE"),
mesmo aparecendo como online; o monitor engana porque toca os proxies, mas a exportação sai PRETA sem aviso.
Reconectar no mesmo caminho resolve."""
import os

PASTAS_DO_DRIVE = ("Drives compartilhados", "Shared drives", "Meu Drive", "My Drive")


def letra_drive():
    """Letra do Google Drive para computador ("G:" na maioria das máquinas, mas não em todas). None se não estiver ligado."""
    for letra in "GHIJKLMNOPQRSTUVWXYZDEF":
        if any(os.path.isdir(f"{letra}:\\{n}") for n in PASTAS_DO_DRIVE):
            return f"{letra}:"
    return None


def reconectar(fc, prefixo_caminho):
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

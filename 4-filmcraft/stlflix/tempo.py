"""Unidades de tempo do FilmCraft: 254.016.000.000 ticks por segundo; a timeline mostra timecode em frames nominais."""
T = 254_016_000_000


def fps(seq):
    fr = seq["settings"]["frame_rate"]
    return fr["num"] / fr["den"]


def frame_ticks(seq):
    fr = seq["settings"]["frame_rate"]
    return round(T * fr["den"] / fr["num"])


def tc(seg, fps_real=24000 / 1001):
    """Segundos → timecode MM:SS:FF da timeline (frames nominais, ex.: 24 em 23,976)."""
    nominal = round(fps_real)
    f = round(seg * fps_real)
    return f"{f // (nominal * 60):02d}:{f // nominal % 60:02d}:{f % nominal:02d}"


def mmss(seg):
    """Segundos → MM:SS.d (arredonda antes, para 59,96 s não virar ':60.0')."""
    d = round(seg * 10)
    return f"{d // 600:02d}:{d % 600 / 10:04.1f}"


def hms(seg):
    return f"{int(seg // 3600):02d}:{int(seg // 60) % 60:02d}:{int(seg % 60):02d}"

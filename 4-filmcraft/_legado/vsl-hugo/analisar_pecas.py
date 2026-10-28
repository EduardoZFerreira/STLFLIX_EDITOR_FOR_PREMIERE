"""Analyse the 3D-piece showcase takes (IMG_52xx.MOV, static tripod shots of a table): per sampled frame,
foreground = difference from the empty-table background, minus skin; reports piece area, piece centroid
(x in source px) and sharpness, then proposes usable segments and a smoothed 9:16 crop track.
Usage: python analisar_pecas.py [--replan] [names]   -> pecas/an_<name>.json (+ prints the plan)
       --replan reuses the saved samples (no decoding) and only redoes segments + crop track
"""
import json, os, subprocess, sys
import cv2
import numpy as np

D = "G:/Drives compartilhados/MKT 2/STUDIO/00 - ASSETS/11. Assets Freela/Peças/02/"
HERE = os.path.dirname(os.path.abspath(__file__))
FILES = ["IMG_5228", "IMG_5229", "IMG_5230", "IMG_5231", "IMG_5232", "IMG_5233", "IMG_5234", "IMG_5235",
         "IMG_5236", "IMG_5237", "IMG_5238", "IMG_5239", "IMG_5241", "IMG_5242"]
W, H, RATE = 480, 270, 6.0
# empty-table reference ranges: 4K set (same framing for 5228-5239) and the 1080p set (5241/5242)
BG = {"4k": ("IMG_5230", 55.0, 100.0), "hd": ("IMG_5242", 42.0, 50.0)}
# reviewed by hand (crop review sheet): drops close-up blur, stretches where only hands and a tiny piece show,
# and in IMG_5242 the presenter walking through the shot
MANUAL = {"IMG_5229": [[0.2, 5.8], [12.0, 19.5]], "IMG_5230": [[0.2, 18.5], [42.5, 46.5]], "IMG_5231": [[1.8, 37.5]],
          "IMG_5232": [[5.5, 25.0]], "IMG_5233": [[4.0, 23.8]], "IMG_5236": [[0.2, 31.2], [33.4, 46.9], [53.5, 60.4]],
          "IMG_5239": [[1.6, 14.8], [16.8, 20.8]], "IMG_5242": [[0.3, 39.7], [63.5, 94.3], [105.5, 120.5], [135.3, 160.7]],
          "IMG_5241": []}


def frames(name, a=None, b=None):
    cmd = ["ffmpeg", "-v", "error"]
    if a is not None:
        cmd += ["-ss", str(a), "-to", str(b)]
    cmd += ["-i", D + name + ".MOV", "-vf", f"fps={RATE},scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def background(key):
    name, a, b = BG[key]
    fr = frames(name, a, b).astype(np.float32)
    bg = np.median(fr, axis=0)
    flicker = (fr.std(axis=0).max(axis=2) > 6).astype(np.uint8)
    flicker = cv2.dilate(flicker, np.ones((9, 9), np.uint8))
    return cv2.GaussianBlur(bg, (5, 5), 0), flicker


def analyse(name, bg, flicker, src_w):
    fr = frames(name)
    out = []
    for k, f in enumerate(fr):
        g = cv2.GaussianBlur(f.astype(np.float32), (5, 5), 0)
        diff = np.abs(g - bg).max(axis=2)
        fg = ((diff > 28) & (flicker == 0)).astype(np.uint8)
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        skin = (h <= 14) & (s >= 35) & (s <= 170) & (v >= 70)
        tattoo = (s < 60) & (v < 110)          # dark, desaturated ink on the forearm
        piece = fg & ~skin & ~tattoo
        area_all = fg.mean()
        area = piece.mean()
        wgt = piece * (s.astype(np.float32) + 60)
        cx = float((wgt.sum(axis=0) * np.arange(W)).sum() / wgt.sum()) * src_w / W if wgt.sum() > 0 else None
        ys = np.nonzero(piece.any(axis=1))[0]
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        sharp = float(cv2.Laplacian(gray, cv2.CV_64F)[piece.astype(bool)].var()) if piece.sum() > 30 else 0.0
        out.append(dict(t=round(k / RATE, 3), area=round(float(area), 4), area_all=round(float(area_all), 4),
                        cx=None if cx is None else round(cx, 1), sharp=round(sharp, 1),
                        y0=int(ys[0]) if len(ys) else None))
    return out


def segments(samples, dur):
    """Good = a piece is visible (not an empty table), the frame isn't swamped (lens blocked / person in shot)."""
    good = [s["area"] > 0.018 and s["area_all"] < 0.40 and s["cx"] is not None for s in samples]
    # close 1-s holes, then keep runs >= 2.5 s, trimmed 0.25 s each side
    n, segs, i = len(good), [], 0
    hole = int(RATE)
    k = 0
    while k < n:
        if not good[k]:
            j = k
            while j < n and not good[j]:
                j += 1
            if 0 < k and j < n and j - k <= hole:
                for m in range(k, j):
                    good[m] = True
            k = j
        else:
            k += 1
    while i < n:
        if good[i]:
            j = i
            while j < n and good[j]:
                j += 1
            a, b = samples[i]["t"] + 0.25, min(dur, samples[j - 1]["t"] + 1 / RATE) - 0.25
            if b - a >= 2.5:
                segs.append([round(a, 2), round(b, 2)])
            i = j
        else:
            i += 1
    return segs


def track(samples, a, b, src_w, half):
    """Smoothed crop-centre keys [(t, cx)] inside [a, b]: median-5 + EMA, a key every 0.5 s when it moved > 3 %."""
    pts = [(s["t"], s["cx"]) for s in samples if a - 0.5 <= s["t"] <= b + 0.5 and s["cx"] is not None]
    if not pts:
        return [(a, src_w / 2)]
    xs = np.array([x for _, x in pts])
    med = np.array([np.median(xs[max(0, i - 2):i + 3]) for i in range(len(xs))])
    ema, e = [], med[0]
    for x in med:
        e = 0.6 * e + 0.4 * x
        ema.append(e)
    keys, last_t = [], -9
    for (t, _), x in zip(pts, ema):
        x = float(np.clip(x, half, src_w - half))
        t = min(max(t, a), b)
        if not keys or (t - last_t >= 0.5 and abs(x - keys[-1][1]) > 0.03 * src_w):
            keys.append((round(t, 2), round(x, 1)))
            last_t = t
    return keys


if __name__ == "__main__":
    os.makedirs(os.path.join(HERE, "pecas"), exist_ok=True)
    replan = "--replan" in sys.argv
    names = [a for a in sys.argv[1:] if not a.startswith("--")] or FILES
    bgs = {} if replan else {k: background(k) for k in BG}
    for name in names:
        hd = name in ("IMG_5241", "IMG_5242")
        src_w = 1920 if hd else 3840
        half = (2160 / (3840 / (1080 if hd else 2160))) / 2        # half the visible 9:16 width, in source px
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    D + name + ".MOV"], capture_output=True, text=True).stdout)
        if replan:
            smp = json.load(open(os.path.join(HERE, "pecas", f"an_{name}.json"), encoding="utf-8"))["samples"]
        else:
            smp = analyse(name, *bgs["hd" if hd else "4k"], src_w)
        segs = MANUAL[name] if name in MANUAL else segments(smp, dur)
        plan = [dict(a=a, b=b, keys=track(smp, a, b, src_w, half)) for a, b in segs]
        json.dump(dict(name=name, dur=dur, src_w=src_w, samples=smp, plan=plan),
                  open(os.path.join(HERE, "pecas", f"an_{name}.json"), "w"), indent=0)
        tot = sum(p["b"] - p["a"] for p in plan)
        print(f"{name} ({dur:5.1f}s): {len(plan)} trechos, {tot:5.1f}s úteis -> " +
              " ".join(f"[{p['a']:.1f}-{p['b']:.1f}]" for p in plan))

"""Turn an analysis (analisar_broll.py) into a vertical-reframe plan: a list of segments covering the whole video,
each with a mode (crop / track / zoom / fit_blur), its geometry and an optional review reason.
Usage: python decidir_broll.py <prefix> [...]   -> writes <prefix>_plan.json and prints a summary
"""
import json, sys
import numpy as np

SRC_W, SRC_H = 1920, 1080
CROP_W = 608                       # full-height 9:16 window in a 1920x1080 frame
ZOOM_W, ZOOM_H = 406, 722          # 1.5x tighter window for screen recordings
OUT_FPS = 24000 / 1001
MIN_HOLD = 1.5                     # seconds a speaker crop must last
MIN_FACE_H = 0.09                  # smaller faces are ignored (facecams, background people)


def snap(t):
    return round(t * OUT_FPS) / OUT_FPS


def crop_x(cx):
    return int(np.clip(round(cx * SRC_W - CROP_W / 2), 0, SRC_W - CROP_W)) // 2 * 2


def tracks_of(samples, min_h):
    pts = [(i, f) for i, s in enumerate(samples) for f in s["faces"] if f["h"] >= min_h]
    groups = []
    for i, f in sorted(pts, key=lambda p: p[1]["x"]):
        g = next((g for g in groups if abs(np.median([q["x"] for _, q in g]) - f["x"]) < 0.08), None)
        (g.append((i, f)) if g is not None else groups.append([(i, f)]))
    out = []
    for g in groups:
        idx = {i for i, _ in g}
        pres = len(idx) / max(1, len(samples))
        if pres >= 0.3:
            out.append({"x": float(np.median([f["x"] for _, f in g])), "h": float(np.median([f["h"] for _, f in g])),
                        "w": float(np.median([f["w"] for _, f in g])), "pres": pres, "items": g})
    return out


ENV = None   # audio envelope at 8 Hz (set per file in build)


def envelope(src, n):
    import subprocess
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
                          "-af", "highpass=f=150,lowpass=f=4000", "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
    win = 2000
    m = len(a) // win
    e = np.sqrt((a[:m * win].reshape(m, win) ** 2).mean(1))
    e = np.pad(e, (0, max(0, n - m)))[:n]
    return e


def plan_shot(a, b, samples, act, i0=0):
    n = len(samples)
    if n == 0:
        return [(a, b, {"mode": "crop", "x": crop_x(0.5)}, "plano curto sem amostra")]
    is_screen = np.mean([s["bright"] > 0.55 and s["sat"] < 0.22 and s["edges"] > 0.05 for s in samples]) > 0.5
    trs = tracks_of(samples, 0.2 if is_screen else MIN_FACE_H)
    if is_screen or not trs:
        grid = act.astype(np.float32).sum(0)
        if is_screen:
            grid[18:, :14] = 0                     # ignore the facecam corner (bottom-left)
        if grid.sum() > 1e-3 and grid.max() > 4 * grid.mean():
            ys, xs = np.mgrid[0:27, 0:48]
            cx, cy = (grid * (xs + 0.5)).sum() / grid.sum() / 48, (grid * (ys + 0.5)).sum() / grid.sum() / 27
        else:
            cx, cy = 0.5, 0.5
        if is_screen:
            # follow the active area: one key every 2 s (activity centroid), smoothed over neighbours
            ys, xs = np.mgrid[0:27, 0:48]
            keys, last = [], (cx, cy)
            for k0 in range(0, n, 16):
                g = act[k0:k0 + 16].astype(np.float32).sum(0)
                g[18:, :14] = 0
                if g.sum() > 1e-3 and g.max() > 4 * g.mean():
                    last = ((g * (xs + 0.5)).sum() / g.sum() / 48, (g * (ys + 0.5)).sum() / g.sum() / 27)
                keys.append((samples[k0]["t"] - a, last[0], last[1]))
            sm = [(t, float(np.mean([k[1] for k in keys[max(0, i - 1):i + 2]])),
                   float(np.mean([k[2] for k in keys[max(0, i - 1):i + 2]]))) for i, (t, _, _) in enumerate(keys)]
            pts = [(float(t), int(np.clip(x * SRC_W - ZOOM_W / 2, 0, SRC_W - ZOOM_W)) // 2 * 2,
                    int(np.clip(y * SRC_H - ZOOM_H / 2, 0, SRC_H - ZOOM_H)) // 2 * 2) for t, x, y in sm]
            return [(a, b, {"mode": "zoom", "keys": pts}, "tela: zoom acompanhando a área com movimento")]
        if np.mean([s["sat"] for s in samples]) > 0.25 or np.mean([s["edges"] for s in samples]) < 0.03:
            return [(a, b, {"mode": "fit_blur"}, "sem rosto: tela inteira com fundo desfocado")]
        return [(a, b, {"mode": "crop", "x": crop_x(cx)}, "sem rosto: recorte na área com movimento")]
    if len(trs) == 1:
        t = trs[0]
        xs = np.array([f["x"] for _, f in sorted(t["items"], key=lambda p: p[0])])
        if xs.std() < 0.05:
            return [(a, b, {"mode": "crop", "x": crop_x(t["x"])}, None)]
        # follow a moving person: 1 key per second, smoothed
        per_s = {}
        for i, f in t["items"]:
            per_s.setdefault(int(samples[i]["t"] - a), []).append(f["x"])
        keys = sorted((k, float(np.median(v))) for k, v in per_s.items())
        sm = [(k, float(np.mean([v for kk, v in keys if abs(kk - k) <= 1]))) for k, _ in keys]
        return [(a, b, {"mode": "track", "keys": [(float(k), crop_x(x)) for k, x in sm]}, None)]
    # 2+ people: both in frame when they fit, else follow the speaker
    left, right = min(trs, key=lambda t: t["x"]), max(trs, key=lambda t: t["x"])
    if (right["x"] + right["w"] / 2) - (left["x"] - left["w"] / 2) <= CROP_W / SRC_W * 0.92:
        return [(a, b, {"mode": "crop", "x": crop_x((left["x"] + right["x"]) / 2)}, None)]
    mouth = np.full((len(trs), n), np.nan)
    for k, t in enumerate(trs):
        for i, f in t["items"]:
            v = f.get("jaw") if f.get("jaw") is not None else f.get("lip")
            if v is not None:
                mouth[k, i] = v
    act_m = np.zeros_like(mouth)
    env = ENV[i0:i0 + n] if ENV is not None else np.zeros(n)
    for k in range(len(trs)):
        for i in range(n):
            lo, hi = max(0, i - 8), min(n, i + 9)             # +-1 s window
            w, e = mouth[k, lo:hi], env[lo:hi]
            ok = ~np.isnan(w)
            if ok.sum() < 5:
                act_m[k, i] = 0.0; continue
            sd = w[ok].std()
            corr = np.corrcoef(w[ok], e[ok])[0, 1] if sd > 1e-4 and e[ok].std() > 1e-6 else 0.0
            act_m[k, i] = sd * (1 + 2 * max(0.0, np.nan_to_num(corr)))   # mouth movement, boosted when in sync with the voice
    cur = int(np.argmax([t["h"] for t in trs]))          # start on the biggest face
    choice, decisive = [], 0
    for i, s in enumerate(samples):
        sc = act_m[:, i]
        best = int(np.argmax(sc))
        srt = np.sort(sc)[::-1]
        if s["speech"] and srt[0] > 0.02 and srt[0] > 1.3 * (srt[1] + 1e-6):
            cur = best; decisive += 1
        choice.append(cur)
    # enforce minimum hold
    runs = []
    for i, c in enumerate(choice):
        if runs and runs[-1][0] == c:
            runs[-1][2] = i
        else:
            runs.append([c, i, i])
    hold = int(MIN_HOLD * 8)
    merged = []
    for r in runs:
        if merged and (r[2] - r[1] + 1) < hold:
            merged[-1][2] = r[2]
        elif merged and merged[-1][0] == r[0]:
            merged[-1][2] = r[2]
        else:
            merged.append(list(r))
    segs = []
    for k, (c, i0, i1) in enumerate(merged):
        s0 = a if k == 0 else samples[i0]["t"]
        s1 = b if k == len(merged) - 1 else samples[merged[k + 1][1]]["t"]
        segs.append((s0, s1, {"mode": "crop", "x": crop_x(trs[c]["x"])}, None))
    if decisive / n < 0.15:
        segs = [(s0, s1, g, "falante incerto (2+ pessoas)") for s0, s1, g, _ in segs]
    return segs


def build(prefix):
    d = json.load(open(prefix + ".json", encoding="utf-8"))
    act = np.load(prefix + "_act.npy")
    global ENV
    ENV = envelope(d["src"], len(d["samples"]))
    S = d["samples"]
    segs = []
    for a, b in d["shots"]:
        idx = [i for i, s in enumerate(S) if a <= s["t"] < b]
        segs += plan_shot(a, b, [S[i] for i in idx], act[idx] if idx else np.zeros((1, 27, 48)), idx[0] if idx else 0)
    # snap to the output frame grid, drop empty pieces, merge equal neighbours
    out = []
    for a, b, g, why in segs:
        a, b = snap(a), snap(b)
        if b - a < 1 / OUT_FPS:
            continue
        if out and out[-1]["geo"] == g and out[-1]["why"] == why:
            out[-1]["b"] = b
        else:
            out.append({"a": a, "b": b, "geo": g, "why": why})
    out[0]["a"] = 0.0
    for p, q in zip(out, out[1:]):
        q["a"] = p["b"]
    out[-1]["b"] = snap(d["duration"])
    json.dump({"src": d["src"], "duration": d["duration"], "segments": out}, open(prefix + "_plan.json", "w", encoding="utf-8"), indent=1)
    modes = {}
    for s in out:
        modes[s["geo"]["mode"]] = modes.get(s["geo"]["mode"], 0) + 1
    rev = [s for s in out if s["why"]]
    print(f"{prefix.split('an_')[-1]:30s} {len(out):4d} trechos {modes} | revisar: {len(rev)}")
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(p)

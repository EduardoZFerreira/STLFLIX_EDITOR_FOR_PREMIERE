"""Review sheet of the planned 9:16 crops for the piece takes: one row per file, a crop every STEP s inside the
kept segments (gaps marked with a red bar). Usage: python revisar_pecas.py out.png [names]"""
import json, os, subprocess, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = "G:/Drives compartilhados/MKT 2/STUDIO/00 - ASSETS/11. Assets Freela/Peças/02/"
STEP, TW, TH, PER_ROW = 1.5, 81, 144, 24


def cx_at(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, x0), (t1, x1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            return x0 + (x1 - x0) * (t - t0) / (t1 - t0)
    return keys[-1][1]


rows = []
for name in (sys.argv[2:] or [f[3:-5] for f in sorted(os.listdir(os.path.join(HERE, "pecas"))) if f.startswith("an_")]):
    an = json.load(open(os.path.join(HERE, "pecas", f"an_{name}.json"), encoding="utf-8"))
    if not an["plan"]:
        continue
    sw = an["src_w"]
    half = (2160 / (3840 / (sw * 9 / 16))) / 2 * (960 / sw)          # half crop width at the 960-px preview
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", D + name + ".MOV", "-vf", f"fps={1 / STEP},scale=960:540",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 540, 960, 3)
    tiles = []
    for k, p in enumerate(an["plan"]):
        if k:
            tiles.append(np.full((TH, 6, 3), (0, 0, 255), np.uint8))
        t = p["a"]
        while t < p["b"] and int(t / STEP) < len(fr):
            f = fr[int(t / STEP)]
            c = cx_at(p["keys"], t) * 960 / sw
            x0 = int(round(c - half))
            crop = cv2.resize(f[:, max(0, x0):x0 + int(2 * half)], (TW, TH))
            cv2.putText(crop, f"{t:.0f}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)
            tiles.append(crop)
            t += STEP
    strip = np.hstack(tiles)
    lab = np.zeros((16, strip.shape[1], 3), np.uint8)
    cv2.putText(lab, name, (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    W = PER_ROW * TW + 24
    for i in range(0, strip.shape[1], W):
        part = strip[:, i:i + W]
        part = np.hstack([part, np.zeros((TH, W - part.shape[1], 3), np.uint8)])
        rows.append(np.vstack([lab[:, i:i + W] if lab[:, i:i + W].shape[1] == W else np.zeros((16, W, 3), np.uint8), part])
                    if i == 0 else part)
cv2.imwrite(sys.argv[1], np.vstack(rows))
print(sys.argv[1], len(rows), "linhas")

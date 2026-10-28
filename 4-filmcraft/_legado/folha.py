"""Contact sheet of a source range: frames every `step` s (16:9 thumbnails, timestamp burned in).
Usage: python folha.py <video> <start> <end> <step> <out.png>"""
import subprocess, sys
import cv2
import numpy as np
src, a, b, step, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
tiles, t = [], a
while t <= b:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=384:-2", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    if raw:
        h = len(raw) // (384 * 3)
        img = np.frombuffer(raw, np.uint8).reshape(h, 384, 3).copy()
        if h > 216: img = cv2.resize(img, (int(384 * 216 / h), 216)); img = cv2.copyMakeBorder(img, 0, 0, 0, 384 - img.shape[1], cv2.BORDER_CONSTANT)
        cv2.putText(img, f"{int(t // 60)}:{t % 60:04.1f}", (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        tiles.append(img[:216])
    t += step
cols = 6
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]))
print(out, len(tiles))

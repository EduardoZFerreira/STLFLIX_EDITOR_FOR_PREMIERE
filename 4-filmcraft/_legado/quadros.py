"""Grid of full frames (16:9 sources) with x gridlines every 160 px, to pick 9:16 crop centres.
Usage: python quadros.py out.png "file|sec|label" ..."""
import subprocess, sys, cv2, numpy as np
B = "G:/Drives compartilhados/GROWTH 2026/1. Campanhas/[BRA] Brasil/[BRA] Black Friday 2026/VSLs/659_[BLACK26]/Brutas/B - Rolls/"
tiles = []
for spec in sys.argv[2:]:
    f, t, lab = spec.split("|")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", t, "-i", B + f + ".mp4", "-frames:v", "1", "-vf", "scale=640:360", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(360, 640, 3).copy()
    for x in range(160, 1920, 160):
        cv2.line(img, (x // 3, 0), (x // 3, 359), (0, 255, 255) if x % 480 == 0 else (0, 160, 160), 1)
        cv2.putText(img, str(x), (x // 3 + 2, 352), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
    for y in (270, 540, 810):
        cv2.line(img, (0, y // 3), (639, y // 3), (255, 0, 255), 1)
    cv2.putText(img, lab, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
    tiles.append(img)
while len(tiles) % 3: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(sys.argv[1], np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]))

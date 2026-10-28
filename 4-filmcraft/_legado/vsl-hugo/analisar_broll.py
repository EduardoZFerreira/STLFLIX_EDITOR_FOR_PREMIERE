"""Analyse a 16:9 B-roll for vertical reframing.

Outputs <prefix>.json (shots, per-sample faces with mouth openness, speech flag, picture stats) and
<prefix>_act.npy (per-sample motion grid 48x27, for screen recordings).
Usage: python analisar_broll.py <video> <prefix>
"""
import json, os, subprocess, sys
import cv2
import numpy as np
from mediapipe import Image, ImageFormat
from mediapipe.tasks.python import BaseOptions, vision
from scenedetect import AdaptiveDetector, detect

HERE = os.path.dirname(os.path.abspath(__file__))
SRC, PREFIX = sys.argv[1], sys.argv[2]
FPS_S, W, H = 8, 960, 540          # analysis sampling rate and size (source is 1920x1080)

# 1) shots (min length 0.6 s so flashes and whip transitions do not count as cuts)
fps_src = cv2.VideoCapture(SRC).get(cv2.CAP_PROP_FPS) or 60
scenes = detect(SRC, AdaptiveDetector(min_scene_len=int(0.6 * fps_src)))
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC],
                           capture_output=True, text=True).stdout)
shots = [[s.get_seconds(), e.get_seconds()] for s, e in scenes] or [[0.0, dur]]

# 2) speech activity per sample (125 ms windows)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vn", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True).stdout
a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
win = 16000 // FPS_S
n_a = len(a) // win
db = 20 * np.log10(np.sqrt((a[:n_a * win].reshape(n_a, win) ** 2).mean(1)) + 1e-9)
speech = (db > np.percentile(db, 15) + 15).tolist()

# 3) faces + mouth + motion + picture stats per sample
det = cv2.FaceDetectorYN.create(os.path.join(HERE, "models", "face_detection_yunet_2023mar.onnx"), "", (W, H), 0.6)
lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=os.path.join(HERE, "models", "face_landmarker.task")),
    running_mode=vision.RunningMode.VIDEO, num_faces=4, output_face_blendshapes=True,
    min_face_detection_confidence=0.4, min_face_presence_confidence=0.4))
proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-an", "-vf", f"fps={FPS_S},scale={W}:{H}",
                         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
samples, acts, prev = [], [], None
k = 0
while True:
    buf = proc.stdout.read(W * H * 3)
    if len(buf) < W * H * 3:
        break
    rgb = np.frombuffer(buf, dtype=np.uint8).reshape(H, W, 3)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    t = k / FPS_S
    faces = []
    _, yu = det.detect(bgr)
    for f in (yu if yu is not None else []):
        x, y, w, h = [float(v) for v in f[:4]]
        faces.append({"x": (x + w / 2) / W, "y": (y + h / 2) / H, "h": h / H, "w": w / W, "jaw": None, "src": "yunet"})
    res = lm.detect_for_video(Image(image_format=ImageFormat.SRGB, data=np.ascontiguousarray(rgb)), int(t * 1000))
    for i, pts in enumerate(res.face_landmarks or []):
        xs, ys = [p.x for p in pts], [p.y for p in pts]
        cx, cy, fh = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(ys) - min(ys)
        jaw = next((b.score for b in res.face_blendshapes[i] if b.category_name == "jawOpen"), None) if res.face_blendshapes else None
        lip = abs(pts[14].y - pts[13].y) / max(fh, 1e-3)          # inner-lip gap / face height
        best = min(faces, key=lambda f: abs(f["x"] - cx) + abs(f["y"] - cy), default=None)
        if best is not None and abs(best["x"] - cx) < 0.08 and abs(best["y"] - cy) < 0.12:
            best.update(jaw=jaw, lip=lip, src="both")
        else:
            faces.append({"x": cx, "y": cy, "h": fh, "w": max(xs) - min(xs), "jaw": jaw, "lip": lip, "src": "mesh"})
    g = cv2.resize(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (240, 135)).astype(np.float32)
    act = np.zeros((27, 48), np.float32) if prev is None else cv2.resize(np.abs(g - prev), (48, 27), interpolation=cv2.INTER_AREA)
    prev = g
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    edges = cv2.Canny(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), 80, 160)
    samples.append({"t": round(t, 3), "faces": faces, "speech": bool(speech[k]) if k < len(speech) else False,
                    "bright": float(hsv[..., 2].mean() / 255), "sat": float(hsv[..., 1].mean() / 255),
                    "edges": float((edges > 0).mean())})
    acts.append(act)
    k += 1
proc.wait()
np.save(PREFIX + "_act.npy", np.array(acts, dtype=np.float16))
json.dump({"src": SRC, "duration": dur, "fps_src": fps_src, "fps_samples": FPS_S, "shots": shots, "samples": samples},
          open(PREFIX + ".json", "w", encoding="utf-8"))
print(f"{os.path.basename(SRC)}: {len(shots)} planos, {len(samples)} amostras, "
      f"{sum(1 for s in samples if s['faces'])} com rosto")

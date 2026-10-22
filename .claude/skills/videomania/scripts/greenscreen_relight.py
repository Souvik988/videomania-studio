"""Relight a keyed presenter so they sit in the background plate (Video Mania).

Grade (darker, warmer, lower body falls into shadow) plus edge light that matches the plate:
warm orange from the shelf lights on the left, cool blue from the PC on the right, a faint warm
top light. Reads part_*.webm (VP9 alpha), writes lit_*.webm.
"""
import subprocess, sys
import cv2
import numpy as np

W, H = 1920, 1080
src, dst = sys.argv[1], sys.argv[2]

yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
body_shade = (1.0 - 0.28 * np.clip((yy - 0.62) / 0.38, 0, 1) ** 1.4)          # lower body darker
side = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
GRADE = np.array([0.80, 0.86, 0.94], np.float32)                                  # BGR: warm, darker
ORANGE = np.array([40, 135, 255], np.float32)
BLUE = np.array([255, 150, 70], np.float32)

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", src,
                        "-f", "rawvideo", "-pix_fmt", "bgra", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                        "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "libvpx-vp9",
                        "-pix_fmt", "yuva420p", "-crf", "18", "-b:v", "0", "-row-mt", "1",
                        "-deadline", "good", "-cpu-used", "4", "-auto-alt-ref", "0", dst],
                       stdin=subprocess.PIPE)
n = 0
while True:
    buf = dec.stdout.read(W * H * 4)
    if len(buf) < W * H * 4:
        break
    f = np.frombuffer(buf, np.uint8).reshape(H, W, 4)
    rgb = f[..., :3].astype(np.float32)
    a = f[..., 3].astype(np.float32) / 255.0

    lum = rgb.mean(-1, keepdims=True)
    rgb = lum + (rgb - lum) * 0.93                                                 # slight desat
    rgb = (rgb / 255.0) ** 1.06 * 255.0                                            # deeper mids
    rgb = rgb * GRADE * body_shade[..., None]

    ab = cv2.GaussianBlur(a, (0, 0), 7)
    band = np.clip(a * (1.0 - ab) * 3.2, 0, 1)                                     # inner edge band
    gx = cv2.Sobel(ab, cv2.CV_32F, 1, 0, ksize=5) * 0.06
    gy = cv2.Sobel(ab, cv2.CV_32F, 0, 1, ksize=5) * 0.06
    wl = band * np.clip(gx, 0, 1) * np.clip(1.1 - side, 0, 1)                      # left-facing
    wr = band * np.clip(-gx, 0, 1) * np.clip(1.1 + side, 0, 1)                     # right-facing
    wt = band * np.clip(gy, 0, 1)                                                  # top-facing
    rgb = rgb + wl[..., None] * ORANGE * 0.55 + wr[..., None] * BLUE * 0.38 + wt[..., None] * ORANGE * 0.22

    out = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), f[..., 3]])
    enc.stdin.write(out.tobytes())
    n += 1
enc.stdin.close(); enc.wait(); print("relit", n)

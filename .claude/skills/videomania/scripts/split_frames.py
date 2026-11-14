"""Two-worlds monitor: frames of a split screen whose divider sweeps away while the drawn half turns glossy.

    python split_frames.py <assets_dir> --left gen/code_skill.png --right gen/editor_ui.png [--frames 40]
        -> <assets_dir>/clips/split/f_001.jpg ...   (680x370)

Use on a monitor:  screen: { kind: "frames", src: "assets/clips/split/f_%03d.jpg", count: 40, title: "two_worlds.mp4" }
It is the "split screen of two worlds that merge by the end" device (clip10): left = the world drawn in code
(desaturated and pixelated 5x), right = the generated one; a white divider holds in the middle for 40 % of the
frames, then sweeps off to the right while the left half blends into the glossy picture. Time it so the merge
lands on the line that says "generate / the answer" and the camera is inside the screen by the last frame.
Both inputs are existing assets (reuse before generating), so it costs nothing.
"""
import argparse
import os
from PIL import Image, ImageDraw, ImageEnhance

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("assets")
ap.add_argument("--left", required=True)
ap.add_argument("--right", required=True)
ap.add_argument("--frames", type=int, default=40)
ap.add_argument("--hold", type=float, default=0.4, help="share of the frames the divider stays in the middle")
a = ap.parse_args()
W, H = 680, 370
L = Image.open(os.path.join(a.assets, a.left)).convert("RGB").resize((W, H), Image.LANCZOS)
R = Image.open(os.path.join(a.assets, a.right)).convert("RGB").resize((W, H), Image.LANCZOS)
Ld = ImageEnhance.Color(L).enhance(0.15).resize((W // 5, H // 5), Image.NEAREST).resize((W, H), Image.NEAREST)
out = os.path.join(a.assets, "clips", "split")
os.makedirs(out, exist_ok=True)
for i in range(a.frames):
    t = i / (a.frames - 1)
    k = max(0.0, (t - a.hold) / (1 - a.hold))
    k = k * k * (3 - 2 * k)
    x = int(W * (0.5 + 0.55 * k))
    left = Image.blend(Ld, L, min(1, k * 1.2))
    im = R.copy()
    im.paste(left.crop((0, 0, min(x, W), H)), (0, 0))
    if x < W:
        ImageDraw.Draw(im).rectangle([x - 2, 0, x + 1, H], fill=(255, 255, 255))
    im.save(os.path.join(out, f"f_{i + 1:03d}.jpg"), quality=92)
print(f"{a.frames} frames -> {out}")

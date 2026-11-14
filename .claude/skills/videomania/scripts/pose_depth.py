"""Depth maps for every pose of a picture mascot, so the kit can render it 2.5D (lit relief, real parallax).

    python pose_depth.py assets/mascot/me/poses.json [--blur 2.5] [--bulge 0.35]

For each pose: the sprite is laid on grey, enlarged, run through Depth Anything V2 Small (CPU, same model as
vm_depth.py), and the depth is re-normalised INSIDE the figure only (0 = the part furthest back, 1 = the
nearest), softened, mixed with a "bulge" (distance from the silhouette edge, so limbs read round even where
the model is flat), and cut to the sprite's alpha. Writes <pose>_depth.png and adds "depth" to poses.json.
The kit then displaces the sprite mesh toward the camera and lights it from the set's key light using normals
from this depth: a lit side, a shadow side, darker recesses, a rim - the mascot reads as a 3D toy, not a sticker.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vm_depth  # noqa: E402


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("poses"); ap.add_argument("--blur", type=float, default=2.5); ap.add_argument("--bulge", type=float, default=0.35)
    a = ap.parse_args()
    import onnxruntime as ort
    pj = Path(a.poses); meta = json.loads(pj.read_text(encoding="utf-8")); base = pj.parent
    so = ort.SessionOptions(); so.intra_op_num_threads = 4
    sess = ort.InferenceSession(vm_depth.model_path(), sess_options=so, providers=["CPUExecutionProvider"])
    for name, v in meta["poses"].items():
        im = Image.open(base / v["src"]).convert("RGBA"); W, H = im.size
        alpha = np.asarray(im)[..., 3] > 127
        bg = Image.new("RGBA", im.size, (128, 128, 128, 255)); bg.alpha_composite(im)
        s = 518 / max(W, H); w, h = max(14, round(W * s / 14) * 14), max(14, round(H * s / 14) * 14)
        x = np.asarray(bg.convert("RGB").resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0
        x = ((x - vm_depth.MEAN) / vm_depth.STD).astype(np.float32).transpose(2, 0, 1)[None]
        d = np.squeeze(sess.run(None, {sess.get_inputs()[0].name: x})[0]).astype(np.float32)
        d = np.asarray(Image.fromarray(d).resize((W, H), Image.BICUBIC))
        inside = d[alpha]
        lo, hi = np.percentile(inside, 2), np.percentile(inside, 98)
        d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)
        edge = ndimage.distance_transform_edt(alpha); edge = np.sqrt(np.clip(edge / max(4.0, np.percentile(edge[alpha], 90)), 0, 1))
        d = (1 - a.bulge) * d + a.bulge * edge
        g = Image.fromarray((np.where(alpha, d, 0) * 255).astype("uint8"), "L").filter(ImageFilter.GaussianBlur(a.blur))
        g = Image.fromarray(np.where(alpha, np.asarray(g), 0).astype("uint8"), "L")
        out = base / (Path(v["src"]).stem + "_depth.png"); g.save(out); v["depth"] = out.name
        print(f"{name:<11} depth {out.name}")
    pj.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

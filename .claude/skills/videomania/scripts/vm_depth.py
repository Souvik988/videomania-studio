"""Depth map from one picture, on this machine (no graphics card needed).

    python vm_depth.py picture.png [-o picture_depth.png] [--blur 6] [--size 518]

Runs the Depth Anything V2 Small model through ONNX Runtime on the CPU (first run downloads about
100 MB into <workbench>/pocket/model). Writes a grey picture the same size as the input: white is
near, black is far, stretched to the full range and softened a little so a relief plate made from it
does not tear at the edges of objects.

Use: a relief plate in the voxel-diorama kit (`relief` in a set file or in SHOTS.plates). The kit pushes
the picture back along this map, so a moving camera slides near parts faster than far parts.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import vm_env

REPO = "onnx-community/depth-anything-v2-small"
FILES = ("onnx/model.onnx", "onnx/model_quantized.onnx")
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)


def model_path() -> str:
    from huggingface_hub import hf_hub_download
    cache = vm_env.workbench() / "pocket" / "model"
    last = None
    for f in FILES:
        for local in (True, False):
            try:
                return hf_hub_download(REPO, f, cache_dir=str(cache), local_files_only=local)
            except Exception as ex:   # try the next file or the network
                last = ex
    raise SystemExit(f"could not get the depth model: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picture")
    ap.add_argument("-o", "--out")
    ap.add_argument("--blur", type=float, default=6, help="softening radius in pixels at the output size")
    ap.add_argument("--size", type=int, default=518, help="model input size on the long side (multiple of 14)")
    a = ap.parse_args()

    import numpy as np
    import onnxruntime as ort
    from PIL import Image, ImageFilter

    src = Path(a.picture)
    im = Image.open(src).convert("RGB")
    W, H = im.size
    s = a.size / max(W, H)
    w, h = max(14, round(W * s / 14) * 14), max(14, round(H * s / 14) * 14)
    x = np.asarray(im.resize((w, h), Image.BICUBIC), dtype=np.float32) / 255.0
    x = ((x - MEAN) / STD).astype(np.float32).transpose(2, 0, 1)[None]

    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    sess = ort.InferenceSession(model_path(), sess_options=so, providers=["CPUExecutionProvider"])
    d = sess.run(None, {sess.get_inputs()[0].name: x})[0]
    d = np.squeeze(d).astype(np.float32)
    lo, hi = np.percentile(d, 1), np.percentile(d, 99)
    d = np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1)          # the model gives larger = nearer

    out = Path(a.out) if a.out else src.with_name(src.stem + "_depth.png")
    g = Image.fromarray((d * 255).astype("uint8"), "L").resize((W, H), Image.BICUBIC)
    if a.blur > 0:
        g = g.filter(ImageFilter.GaussianBlur(a.blur))
    g.save(out)
    near = float((d > 0.66).mean()) * 100
    far = float((d < 0.33).mean()) * 100
    print(f"depth: {out}")
    print(f"       near third {near:.0f}% of the picture, far third {far:.0f}% (a good relief has both above 10%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

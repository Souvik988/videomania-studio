"""Cut a ChatGPT pose sheet into clean mascot sprites, all on one pixel scale.

    python pose_sheet.py sheet_a.png --names talk,point,walk,jump,sit_code,think,cheer,wave \
        [sheet_b.png --names run,floor_code,...] -o assets/mascot --tall 170 --ref-pose talk

The sheet: one character, a grid of full-body poses, flat pure magenta #FF00FF background (ask for it in
the prompt; make the sheet with scripts/gpt_image_ref.sh and the approved hero design as --ref so every
pose is the same person). This:
  1. keys out the magenta (and its pink fringe), keeps solid pixels only;
  2. finds each pose as a connected blob (small parts like a raised hand are merged), reads them in rows,
     top to bottom then left to right, and names them in that order;
  3. scales EVERY pose by one factor so --ref-pose is --tall pixels high (so a jump is not bigger than an
     idle), snaps to that pixel grid (crisp, small pixels: 150-200 px tall reads smooth, not blocky);
  4. writes <name>.png per pose, poses.json (sizes, foot anchor) and preview.png (all poses on grey).
Use in a film: SHOTS.cast = { me: { poses: "assets/mascot/poses.json", tall: 10 } } and act with the pose
names (see the kit README "Picture mascots").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


def key_magenta(rgb: np.ndarray) -> np.ndarray:
    r, g, b = (rgb[..., i].astype(int) for i in range(3))
    mag = np.minimum(r, b) - g                      # how magenta a pixel is
    # the background: true magenta only (red and blue both high and close), so purple and pink art survive
    bg = (r > 170) & (b > 170) & (g < 130) & (np.abs(r - b) < 70)
    bg = ndimage.binary_closing(bg, iterations=2)
    # the fringe: magenta-ish pixels touching the background
    near = ndimage.binary_dilation(bg, iterations=2)
    bg |= near & (mag > 40)
    alpha = (~bg).astype(np.uint8)
    alpha = ndimage.binary_opening(alpha, iterations=1).astype(np.uint8)
    return alpha


def blobs(alpha: np.ndarray, n: int) -> list[tuple[slice, slice]]:
    merged = ndimage.binary_dilation(alpha, iterations=max(6, alpha.shape[0] // 90))
    lab, k = ndimage.label(merged)
    objs = ndimage.find_objects(lab)
    sizes = ndimage.sum(alpha, lab, range(1, k + 1))
    keep = [objs[i] for i in np.argsort(-sizes)[:n]]
    # rows: cluster by vertical centre
    keep.sort(key=lambda s: (s[0].start + s[0].stop) / 2)
    rows, cur = [], [keep[0]] if keep else []
    for s in keep[1:]:
        c = (s[0].start + s[0].stop) / 2; c0 = np.mean([(q[0].start + q[0].stop) / 2 for q in cur])
        if abs(c - c0) < alpha.shape[0] * 0.18:
            cur.append(s)
        else:
            rows.append(cur); cur = [s]
    if cur:
        rows.append(cur)
    return [s for row in rows for s in sorted(row, key=lambda q: q[1].start)]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    sheets, names, rest, i = [], [], [], 0
    while i < len(argv):
        if argv[i] == "--names":
            names[-1] = argv[i + 1].split(","); i += 2
        elif argv[i].startswith("-"):
            rest += argv[i:i + 2]; i += 2
        else:
            sheets.append(argv[i]); names.append([]); i += 1
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", required=True); ap.add_argument("--tall", type=int, default=170)
    ap.add_argument("--ref-pose", default=None); ap.add_argument("--margin", type=int, default=4)
    a = ap.parse_args(rest)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    crops = {}
    for sh, nm in zip(sheets, names):
        img = np.array(Image.open(sh).convert("RGB"))
        alpha = key_magenta(img)
        found = blobs(alpha, len(nm))
        if len(found) < len(nm):
            print(f"warning: {sh}: found {len(found)} poses, expected {len(nm)}")
        for name, s in zip(nm, found):
            part = img[s].astype(int)
            spill = np.clip(np.minimum(part[..., 0], part[..., 2]) - part[..., 1] - 8, 0, None)   # despill: pull pink off the edges
            part[..., 0] -= spill; part[..., 2] -= spill
            rgba = np.dstack([np.clip(part, 0, 255).astype(np.uint8), (alpha[s] * 255).astype(np.uint8)])
            ys, xs = np.nonzero(rgba[..., 3])
            crops[name] = rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ref = a.ref_pose or next(iter(crops))
    f = a.tall / crops[ref].shape[0]
    info = {}
    for name, c in crops.items():
        h, w = c.shape[:2]; W, H = max(1, round(w * f)), max(1, round(h * f))
        im = Image.fromarray(c, "RGBA")
        # premultiply so keyed edges do not bleed magenta, then snap alpha to solid / clear
        arr = np.array(im).astype(float); arr[..., :3] *= arr[..., 3:4] / 255
        small = np.array(Image.fromarray(arr.astype(np.uint8), "RGBA").resize((W, H), Image.LANCZOS)).astype(float)
        al = small[..., 3]; rgb = small[..., :3] / np.maximum(al[..., None] / 255, 1e-3)
        res = np.dstack([np.clip(rgb, 0, 255), np.where(al > 110, 255, 0)]).astype(np.uint8)
        m = a.margin
        canvas = np.zeros((H + 2 * m, W + 2 * m, 4), np.uint8); canvas[m:m + H, m:m + W] = res
        Image.fromarray(canvas, "RGBA").save(out / f"{name}.png")
        info[name] = {"src": f"{name}.png", "w": W + 2 * m, "h": H + 2 * m}
    meta = {"ref": ref, "tall_px": a.tall, "scale": round(f, 4), "poses": info}
    (out / "poses.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    # preview
    ims = [Image.open(out / v["src"]) for v in info.values()]
    Wt = sum(i.width for i in ims) + 10 * (len(ims) + 1); Ht = max(i.height for i in ims) + 20
    pv = Image.new("RGBA", (Wt, Ht), (90, 94, 102, 255)); x = 10
    for im in ims:
        pv.alpha_composite(im, (x, Ht - 10 - im.height)); x += im.width + 10
    pv = pv.resize((pv.width * 2, pv.height * 2), Image.NEAREST); pv.save(out / "preview.png")
    print(f"{len(info)} poses at scale {f:.3f} ({ref} = {a.tall} px): " + ", ".join(f"{k} {v['w']}x{v['h']}" for k, v in info.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

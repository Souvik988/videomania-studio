"""Turn aligned pose images of a character into rig parts for talking-character.js (MKTC).

You (or ChatGPT, see references/talking-head-reels.md) produce ONE character image, then edit it in
the same thread so that only one thing changes per image: the mouth shape, or the eyes. This script
finds what changed, cuts small feathered patches, and writes parts.json.

Usage:
  character_parts.py --dir poses/ --out parts/ [--thr 28] [--selftest]

Inputs in --dir (PNG, identical size and framing, transparent or flat background):
  head.png          rest pose: eyes open, mouth closed (this is mouth X)
  mouth_<L>.png     any of A B C D E F G H: the same image with that mouth shape (at least C and D)
  eyes_closed.png   optional: the same image with eyes shut

Outputs in --out: head.png, mouth_X.png.. (patches), lids.png, parts.json
  parts.json = {head, aspect, mouthBox{x,y,w,h}, eyeBox, mouths{X..H}, lids, alignment{...}}
  boxes are fractions of the head image, ready for MKTC.rig(..., {parts, base}).

alignment.outside_ratio is the share of changed pixels OUTSIDE the mouth/eye boxes. Above ~1.5% the
poses drifted (the image moved, the face changed) and the patches will shimmer: regenerate.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

LETTERS = "ABCDEFGH"
FALLBACK = {"A": "XB", "B": "CX", "C": "BD", "D": "CE", "E": "DC", "F": "EX", "G": "BA", "H": "CB"}


def load(p: Path) -> np.ndarray:
    return np.asarray(Image.open(p).convert("RGBA"), dtype=np.float32)


def flat(a: np.ndarray) -> np.ndarray:
    """composite on mid-grey so transparent regions compare equal"""
    al = a[..., 3:4] / 255.0
    return a[..., :3] * al + 128.0 * (1 - al)


def diff_mask(a: np.ndarray, b: np.ndarray, thr: float) -> np.ndarray:
    d = np.abs(flat(a) - flat(b)).max(axis=2)
    return d > thr


def bbox(mask: np.ndarray, pad: float):
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    h, w = mask.shape
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    px, py = int((x1 - x0) * pad) + 4, int((y1 - y0) * pad) + 4
    return max(0, x0 - px), max(0, y0 - py), min(w, x1 + px), min(h, y1 + py)


def feather(patch: np.ndarray, r: int = 6) -> np.ndarray:
    h, w = patch.shape[:2]
    r = max(1, min(r, h // 3, w // 3))
    ramp_x = np.minimum(1.0, np.minimum(np.arange(w), np.arange(w)[::-1]) / r)
    ramp_y = np.minimum(1.0, np.minimum(np.arange(h), np.arange(h)[::-1]) / r)
    out = patch.copy()
    out[..., 3] *= (ramp_y[:, None] * ramp_x[None, :])
    return out


def save(a: np.ndarray, p: Path):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(p)


def build(src: Path, out: Path, thr: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    head_p = src / "head.png"
    if not head_p.exists():
        raise SystemExit(f"missing {head_p}")
    base = load(head_p)
    H, W = base.shape[:2]
    mouths_src = {L: src / f"mouth_{L}.png" for L in LETTERS if (src / f"mouth_{L}.png").exists()}
    if len(mouths_src) < 2:
        raise SystemExit("need at least two mouth poses (mouth_C.png and mouth_D.png) besides head.png")
    variants = {"X": base}
    masks = {}
    for L, p in mouths_src.items():
        a = load(p)
        if a.shape != base.shape:
            raise SystemExit(f"{p.name} is {a.shape[1]}x{a.shape[0]}, head.png is {W}x{H}: poses must be the same size")
        variants[L] = a
        masks[L] = diff_mask(a, base, thr)
    # cut the box from the typical poses only, so one drifted pose cannot grow the box to the whole face
    areas = {L: int(m.sum()) for L, m in masks.items()}
    med = float(np.median(list(areas.values())))
    union = np.zeros((H, W), bool)
    for L, m in masks.items():
        if areas[L] <= 2.5 * max(med, 1):
            union |= m
    box = bbox(union, 0.12)
    if box is None:
        raise SystemExit("mouth poses are identical to head.png: nothing changed")
    x0, y0, x1, y1 = box
    mouths = {}
    for L, a in variants.items():
        fn = f"mouth_{L}.png"
        save(feather(a[y0:y1, x0:x1].copy()), out / fn)
        mouths[L] = fn
    for L in LETTERS:  # fill gaps from the nearest available shape
        if L not in mouths:
            mouths[L] = mouths[next(c for c in FALLBACK[L] + "XCD" if c in mouths)]
    eye_box = None
    lids = None
    changed_outside = 0
    total_changed = int(union.sum())
    eye_union = np.zeros((H, W), bool)
    ec = src / "eyes_closed.png"
    if ec.exists():
        a = load(ec)
        eye_union = diff_mask(a, base, thr)
        eb = bbox(eye_union, 0.18)
        if eb:
            ex0, ey0, ex1, ey1 = eb
            save(feather(a[ey0:ey1, ex0:ex1].copy(), 4), out / "lids.png")
            lids = "lids.png"
            eye_box = {"x": ex0 / W, "y": ey0 / H, "w": (ex1 - ex0) / W, "h": (ey1 - ey0) / H}
            total_changed += int(eye_union.sum())
    allowed = np.zeros((H, W), bool)
    allowed[y0:y1, x0:x1] = True
    if eye_box:
        allowed[ey0:ey1, ex0:ex1] = True
    # changed pixels of every pose that fall outside the cut boxes
    for a in list(variants.values()) + ([load(ec)] if ec.exists() else []):
        changed_outside = max(changed_outside, int((diff_mask(a, base, thr) & ~allowed).sum()))
    total_changed = sum(areas.values()) + int(eye_union.sum())
    ratio = changed_outside / max(1, total_changed)
    box_frac = ((x1 - x0) * (y1 - y0)) / (W * H)
    if box_frac > 0.25:
        ratio = max(ratio, 1.0)  # a "mouth" bigger than a quarter of the image means the poses are not aligned
    save(base, out / "head.png")
    parts = {"head": "head.png", "aspect": round(H / W, 4),
             "mouthBox": {"x": x0 / W, "y": y0 / H, "w": (x1 - x0) / W, "h": (y1 - y0) / H},
             "eyeBox": eye_box, "mouths": mouths, "lids": lids,
             "alignment": {"outside_ratio": round(ratio, 4), "ok": ratio < 0.015, "poses": sorted(mouths_src), "size": [W, H]}}
    (out / "parts.json").write_text(json.dumps(parts, indent=2), encoding="utf-8")
    return parts


def selftest() -> int:
    """draw a synthetic character, build parts, and check the boxes and the alignment gauge"""
    with tempfile.TemporaryDirectory() as td:
        src, out = Path(td) / "poses", Path(td) / "parts"
        src.mkdir()

        def face(mouth: str | None, eyes_closed=False, drift=0):
            im = Image.new("RGBA", (400, 480), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.ellipse((60 + drift, 40, 340 + drift, 440), fill=(240, 200, 160, 255))
            for ex in (140, 260):
                if eyes_closed:
                    d.line((ex - 22 + drift, 190, ex + 22 + drift, 190), fill=(30, 20, 20, 255), width=6)
                else:
                    d.ellipse((ex - 18 + drift, 170, ex + 18 + drift, 210), fill=(255, 255, 255, 255))
                    d.ellipse((ex - 8 + drift, 180, ex + 8 + drift, 200), fill=(30, 20, 20, 255))
            shapes = {"X": (170, 330, 230, 336), "C": (160, 320, 240, 350), "D": (150, 310, 250, 370), "E": (180, 315, 220, 365)}
            if mouth:
                d.ellipse(tuple(v + (drift if i % 2 == 0 else 0) for i, v in enumerate(shapes[mouth])), fill=(110, 30, 40, 255))
            return im

        face("X").save(src / "head.png")
        for L in "CDE":
            face(L).save(src / f"mouth_{L}.png")
        face("X", eyes_closed=True).save(src / "eyes_closed.png")
        p = build(src, out, 28)
        mb = p["mouthBox"]
        assert 0.3 < mb["x"] < 0.45 and 0.6 < mb["y"] < 0.72, f"mouth box location {mb}"
        assert p["eyeBox"] and 0.15 < p["eyeBox"]["x"] < 0.4, "eye box found"
        assert all(L in p["mouths"] for L in "XABCDEFGH"), "all nine letters mapped"
        assert p["alignment"]["ok"], f"aligned poses pass the gauge: {p['alignment']}"
        assert (out / "parts.json").exists() and (out / "lids.png").exists()
        # a drifted pose must trip the gauge
        face("D", drift=14).save(src / "mouth_D.png")
        p2 = build(src, Path(td) / "parts2", 28)
        assert not p2["alignment"]["ok"], f"drifted pose is flagged: {p2['alignment']}"
    print("character_parts selftest: ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir")
    ap.add_argument("--out")
    ap.add_argument("--thr", type=float, default=28.0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.dir or not a.out:
        ap.error("--dir and --out are required")
    p = build(Path(a.dir), Path(a.out), a.thr)
    al = p["alignment"]
    print(f"character_parts: {len(al['poses'])} mouth poses, eyes {'yes' if p['lids'] else 'no'}, "
          f"outside change {al['outside_ratio']*100:.2f}% -> {'OK' if al['ok'] else 'DRIFT: regenerate the poses'}")
    return 0 if al["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

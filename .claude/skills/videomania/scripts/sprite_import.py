"""Turn a generated character picture into a clean pixel sprite for the voxel-diorama cast.

    python sprite_import.py fox_src.png -o assets/cast/fox.png [--tall 64] [--colors 20] [--key auto] [--outline]

The picture should show one character on a flat background (ask the image model for pure magenta
#FF00FF). This removes the background (the colour of the corners, or --key "#ff00ff"), crops to the
character, snaps it down to a real pixel grid --tall pixels high, limits the palette, makes every pixel
fully solid or fully clear, and with --outline adds a one-pixel dark edge. It prints the size and the
palette, and writes a 6x enlarged preview next to the sprite so you can look at it.

Use it in a film: SHOTS.cast = { fox: { src: "assets/cast/fox.png", tall: 9 } }  (tall = height in voxels)
then name it in a shot's cast like the built-in characters. For hand clean-up or extra frames open the
PNG in Aseprite (<workbench>/tools/aseprite/build/bin/aseprite.exe).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picture")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--tall", type=int, default=64, help="sprite height in pixels (60 or more: house rule)")
    ap.add_argument("--colors", type=int, default=20)
    ap.add_argument("--key", default="auto", help='background colour, "#rrggbb" or auto (taken from the corners)')
    ap.add_argument("--tolerance", type=int, default=70)
    ap.add_argument("--outline", action="store_true")
    a = ap.parse_args()

    import numpy as np
    from PIL import Image

    im = Image.open(a.picture).convert("RGBA")
    px = np.asarray(im).astype(np.int32)
    if a.key == "auto":
        corners = np.array([px[0, 0, :3], px[0, -1, :3], px[-1, 0, :3], px[-1, -1, :3]])
        key = np.median(corners, axis=0)
    else:
        key = np.array([int(a.key[i:i + 2], 16) for i in (1, 3, 5)])
    dist = np.sqrt(((px[:, :, :3] - key) ** 2).sum(axis=2))
    solid = (dist > a.tolerance) & (px[:, :, 3] > 128)
    if solid.mean() < 0.02 or solid.mean() > 0.9:
        raise SystemExit(f"background removal failed (character covers {solid.mean():.0%} of the picture): pass --key or raise/lower --tolerance")
    ys, xs = np.where(solid)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgb = Image.fromarray(px[y0:y1, x0:x1, :3].astype("uint8"), "RGB")
    mask = Image.fromarray((solid[y0:y1, x0:x1] * 255).astype("uint8"), "L")

    h = a.tall
    w = max(1, round(rgb.width * h / rgb.height))
    # shrink with an area average first (the generated "pixels" are many real pixels wide), then fix the palette
    small = rgb.resize((w, h), Image.BOX).quantize(a.colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    m = np.asarray(mask.resize((w, h), Image.BOX)) > 110
    out = np.zeros((h + 2, w + 2, 4), dtype=np.uint8)
    out[1:-1, 1:-1, :3] = np.asarray(small)
    out[1:-1, 1:-1, 3] = m * 255
    # magenta fringe left by the shrink: pull edge pixels that are still close to the key towards their neighbours' darkest tone
    body = out[:, :, 3] > 0
    fringe = body & (np.sqrt(((out[:, :, :3].astype(np.int32) - key) ** 2).sum(axis=2)) < a.tolerance * 1.6)
    out[fringe, 3] = 0
    body = out[:, :, 3] > 0
    if a.outline:
        pad = np.pad(body, 1)
        near = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
        edge = near & ~body
        out[edge] = (18, 12, 20, 255)
    out[out[:, :, 3] == 0] = 0

    dst = Path(a.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    sprite = Image.fromarray(out, "RGBA")
    sprite.save(dst)
    big = Image.new("RGBA", (out.shape[1] * 6, out.shape[0] * 6), (40, 36, 48, 255))
    big.alpha_composite(sprite.resize(big.size, Image.NEAREST))
    prev = dst.with_name(dst.stem + "_preview.png")
    big.convert("RGB").save(prev)
    cols = sorted(Image.fromarray(out[:, :, :3]).getcolors(100000) or [], reverse=True)[:8]
    print(f"sprite:  {dst}  ({out.shape[1]} x {out.shape[0]} px)")
    print(f"preview: {prev}")
    print("palette: " + " ".join("#%02x%02x%02x" % c for _, c in cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())

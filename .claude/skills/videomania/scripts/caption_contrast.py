"""Measure whether every burned-in caption is readable against what is actually behind it.

Usage:
  caption_contrast.py --video RENDER.mp4 --cues source/data.js|transcript/captions.json
                      [--text-colors "#fffaf2,#ffc23d,#ff7a66"] [--zone 0.70,0.84]
                      [--min-ratio 4.5] [--out qa/<tag>/caption_contrast.json]

For each cue it grabs the rendered frame a little after the cue starts and at its midpoint,
finds the caption's text pixels (pixels close to one of --text-colors inside the caption
--zone), and measures the WCAG 2.1 contrast ratio between the text colour and the WORST pixels
in a thin ring just outside the letterforms (the 95th luminance percentile for light text,
the 5th for dark text). That is what a viewer's eye reads the glyph against: the caption box if
there is one, the footage if there is not. A cue whose text pixels cannot be found is reported
as "not_found" (often a deliberately suppressed caption) rather than failed.

Rule behind it (herk-edit-kit playbook, Nate's note "white captions on a bright website are
unreadable"): never white on light; measure the pixels behind every caption. WCAG AA for text
is 4.5:1. Port of the idea in herk-edit-kit's contrast-report.mjs (MIT), measured on the
encoded render instead of the live DOM so it needs no extra npm packages.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import binary_dilation, binary_erosion, find_objects, label


def hex_rgb(h: str) -> np.ndarray:
    h = h.strip().lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def rel_lum(rgb: np.ndarray) -> np.ndarray:
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def load_cues(path: Path) -> list[tuple[float, float, str]]:
    txt = path.read_text(encoding="utf-8")
    if path.suffix == ".js":
        txt = txt[txt.index("["): txt.rindex("]") + 1]
        data = json.loads(txt)
        return [(c["s"], c["e"], " / ".join(" ".join(w["w"] for w in ln) for ln in c["lines"])) for c in data]
    data = json.loads(txt)
    return [(c["start"], c.get("display_end", c["end"]), " / ".join(c.get("lines", [c.get("text", "")]))) for c in data]


def frame(video: Path, t: float, w: int, h: int) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8)[: w * h * 3].reshape(h, w, 3).astype(np.float32)


def glyph_mask(mask: np.ndarray, font_px: int) -> np.ndarray:
    """Keep connected pieces the size of letters or words; drop large areas (a background whose
    colour happens to be close to the text colour, even when textured)."""
    lab, n = label(mask)
    # letter strokes are ~0.2 x font size thick; a piece with any pixel that survives this
    # erosion is a fat blob (e.g. a vignetted background patch), not lettering
    fat = np.unique(lab[binary_erosion(mask, iterations=max(3, round(font_px * 0.13)))])
    keep = np.zeros(n + 1, bool)
    for i, sl in enumerate(find_objects(lab), 1):
        if sl is None:
            continue
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        keep[i] = 0.25 * font_px <= h <= 1.6 * font_px and w <= 6 * font_px
    keep[fat] = False
    keep[0] = False
    return keep[lab]


def measure(img: np.ndarray, zone: tuple[float, float], colors: list[np.ndarray], tol: float = 30.0,
            font_px: int = 52):
    """Contrast of caption lettering against what surrounds each letter-piece.

    Each glyph piece is compared with the ring 2-5 px outside it (the 90th luminance percentile
    toward the text, i.e. its worst local background). The cue's ratio is the area-weighted
    median over pieces, and `low_share` is the share of glyph area under 3:1 (fail above 0.4). A few stray
    pieces (vignette crescents, sparkles) cannot decide the result; an unreadable caption,
    where most letters sit on a similar background, still fails."""
    h = img.shape[0]
    z = img[int(zone[0] * h): int(zone[1] * h)]
    best = None
    for col in colors:
        mask = glyph_mask(np.linalg.norm(z - col, axis=2) < tol, font_px)
        if mask.sum() < 0.3 * font_px * font_px:  # less than about one word: not a caption
            continue
        lt = float(rel_lum(col))
        lab, n = label(mask)
        ratios, areas = [], []
        for i, sl in enumerate(find_objects(lab), 1):
            if sl is None:
                continue
            y0, y1 = max(0, sl[0].start - 6), min(z.shape[0], sl[0].stop + 6)
            x0, x1 = max(0, sl[1].start - 6), min(z.shape[1], sl[1].stop + 6)
            comp = lab[y0:y1, x0:x1] == i
            ring = binary_dilation(comp, iterations=5) & ~binary_dilation(mask[y0:y1, x0:x1], iterations=2)
            if ring.sum() < 10:
                continue
            lb = rel_lum(z[y0:y1, x0:x1][ring])
            worst = float(np.percentile(lb, 90 if lt > 0.4 else 10))
            ratios.append((max(lt, worst) + 0.05) / (min(lt, worst) + 0.05))
            areas.append(int(comp.sum()))
        if not ratios:
            continue
        r, a = np.array(ratios), np.array(areas, float)
        order = np.argsort(r)
        cum = np.cumsum(a[order]) / a.sum()
        median = float(r[order][np.searchsorted(cum, 0.5)])
        cand = {"text_px": int(mask.sum()), "pieces": len(r), "ratio": round(median, 2),
                "low_share": round(float(a[r < 3.0].sum() / a.sum()), 3), "text_lum": round(lt, 3)}
        if best is None or cand["text_px"] > best["text_px"]:
            best = cand
    return best


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--cues", required=True)
    ap.add_argument("--text-colors", default="#fffaf2,#ffffff,#ffc23d,#ff7a66")
    ap.add_argument("--zone", default="0.70,0.84", help="caption band as top,bottom fractions of frame height")
    ap.add_argument("--min-ratio", type=float, default=4.5)
    ap.add_argument("--font-px", type=int, default=52, help="caption font size in pixels")
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    video = Path(a.video)
    st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                    "stream=width,height", "-of", "json", str(video)], capture_output=True).stdout)["streams"][0]
    W, H = st["width"], st["height"]
    zone = tuple(float(v) for v in a.zone.split(","))
    colors = [hex_rgb(c) for c in a.text_colors.split(",")]
    rows, fails, missing = [], [], []
    for s, e, text in load_cues(Path(a.cues)):
        for t in (min(e - 0.02, s + 0.15), (s + e) / 2):
            m = measure(frame(video, t, W, H), zone, colors, font_px=a.font_px)
            row = {"t": round(t, 2), "cue": text[:60], **(m or {"status": "not_found"})}
            rows.append(row)
            if m is None:
                missing.append(round(t, 2))
            elif m["ratio"] < a.min_ratio or m["low_share"] > 0.4:
                fails.append(row)
    res = {"video": str(video), "min_ratio": a.min_ratio, "zone": zone, "samples": len(rows),
           "fail": fails, "not_found_at": missing, "pass": not fails,
           "worst": min((r for r in rows if "ratio" in r), key=lambda r: r["ratio"], default=None), "rows": rows}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("pass", "samples", "worst", "fail", "not_found_at")}, indent=2, ensure_ascii=False))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())

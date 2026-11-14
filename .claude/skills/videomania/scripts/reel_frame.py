"""Reel export for a voxel-diorama film: compose the film at 4:5 (or any size), then sit it in the
middle of a 9:16 phone frame with plain black above and below.

    python reel_frame.py prep    <source_dir> [--size 1080x1350] [--keep 0.82]
    python reel_frame.py pad     <in.mp4> <out.mp4> [--canvas 1080x1920]
    python reel_frame.py restore <source_dir>

Why (user's note on director film v5, 2026-11-14): "the most cinematic format ... 9:16, and in the middle of
it the video. I don't want to transform this video totally into 9:16." Two attempts failed first:
  - the 16:9 film scaled into a 9:16 frame: a thin strip, "still landscape";
  - a full native 1080x1920 re-composition: "transformed totally".
What the user wanted: the film composed for a 4:5 block (1080x1350), so it fills most of the phone, padded to
1080x1920 with black bars (285 px top and bottom). Nothing outside the picture: no captions, frame or plate.

prep    - backs up index.html and shots.js into <project>/_landscape/ (once; never inside source/), rewrites the page size (viewport, #root
          data-width/height, the canvas) and the `size:` line of shots.js to the reel size, and adds
          `portraitKeep` (how much of the landscape width the camera keeps; 0.82 for 4:5). The kit's portrait
          mode then opens the camera vertically and moves words and overlays into the taller frame.
          AFTER prep: snapshot the busy moments and move any card/prop that now sits outside the frame
          (closer to the centre line, e.g. at: [9, 9.5, 2] -> [5.5, 10.5, 3]). Never re-design the film.
pad     - centres the render in the canvas with black bars; video re-encoded (crf 17), audio copied as AAC.
restore - puts the backed-up landscape index.html and shots.js back.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def rd(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def wr(p, txt):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(txt)


def wh(s):
    w, h = s.lower().split("x")
    return int(w), int(h)


def prep(src: Path, size: str, keep: float):
    w, h = wh(size)
    idx, shots = src / "index.html", src / "shots.js"
    bk = src.parent / "_landscape"      # NOT inside source/: hyperframes check rejects a second root HTML there
    bk.mkdir(exist_ok=True)
    land, shots_land = bk / "index.html", bk / "shots.js"
    if not land.exists():
        shutil.copy2(idx, land)
    if not shots_land.exists():
        shutil.copy2(shots, shots_land)
    html = rd(land)
    html, n1 = re.subn(r'width=\d+, height=\d+', f"width={w}, height={h}", html, count=1)
    html, n2 = re.subn(r'(id="root"[^>]*?)data-width="\d+" data-height="\d+"', rf'\1data-width="{w}" data-height="{h}"', html, count=1)
    html, n3 = re.subn(r'(<canvas id="vd-canvas") width="\d+" height="\d+"', rf'\1 width="{w}" height="{h}"', html, count=1)
    if not (n1 and n2 and n3):
        sys.exit(f"index.html: could not find viewport/root/canvas sizes ({n1},{n2},{n3})")
    wr(idx, html)
    js = rd(shots_land)
    js = re.sub(r"\s*portraitKeep:\s*[\d.]+,", "", js)
    js, n = re.subn(r"size:\s*\[\s*\d+\s*,\s*\d+\s*\],", f"size: [{w}, {h}], portraitKeep: {keep},", js, count=1)
    if not n:
        sys.exit("shots.js: no `size: [W, H],` line")
    wr(shots, js)
    print(f"reel page ready: {w}x{h}, portraitKeep {keep}. Snapshot the busy moments before rendering.")


def pad(inp: str, out: str, canvas: str):
    cw, ch = wh(canvas)
    vf = f"scale={cw}:-2:flags=lanczos,pad={cw}:{ch}:0:(oh-ih)/2:black,setsar=1"
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", inp, "-vf", vf, "-c:v", "libx264", "-crf", "17", "-preset", "slow",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"wrote {out} ({cw}x{ch}, film centred, black bars)")


def restore(src: Path):
    bk = src.parent / "_landscape"
    for a, b in (("index.html", "index.html"), ("shots.js", "shots.js")):
        if (bk / a).exists():
            shutil.copy2(bk / a, src / b)
            print(f"restored {b}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("prep"); p.add_argument("source"); p.add_argument("--size", default="1080x1350"); p.add_argument("--keep", type=float, default=0.82)
    p = sp.add_parser("pad"); p.add_argument("inp"); p.add_argument("out"); p.add_argument("--canvas", default="1080x1920")
    p = sp.add_parser("restore"); p.add_argument("source")
    a = ap.parse_args()
    if a.cmd == "prep":
        prep(Path(a.source), a.size, a.keep)
    elif a.cmd == "pad":
        pad(a.inp, a.out, a.canvas)
    else:
        restore(Path(a.source))


if __name__ == "__main__":
    main()

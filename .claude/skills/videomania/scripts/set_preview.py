"""Render a voxel-diorama set from several angles, and compare it with its concept picture.

    python set_preview.py --set cafe [--concept path/to/concept.png] [--out DIR] [--cast]

The set is templates/voxel-diorama/sets/<name>.json (or a path to a .json file, or a built-in set name:
studio, city-night, void). It writes four stills (the set's own "wide" camera, a left and a right
three-quarter view, a top view), a contact sheet, and with --concept a side-by-side picture
(concept | wide render) plus a rough match report: mean colour difference on a 16 x 9 grid (0 = same),
brightness of both, and the dominant colours of each. Look at the side-by-side, then edit the set file.

This is the set builder's loop (crew/04b-set-builder.md): concept -> set.json -> preview -> compare -> fix.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import vm_env

KIT = vm_env.SKILL_DIR / "templates" / "voxel-diorama"
BUILTIN = {"studio", "city-night", "void"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", required=True)
    ap.add_argument("--concept")
    ap.add_argument("--out")
    ap.add_argument("--cast", action="store_true", help="stand the cast on the set's stage mark, for scale")
    a = ap.parse_args()

    src = Path(a.set)
    name = src.stem if src.suffix == ".json" else a.set
    data = None
    if name not in BUILTIN:
        f = src if src.suffix == ".json" else KIT / "sets" / f"{name}.json"
        if not f.exists():
            raise SystemExit(f"set file not found: {f}")
        data = json.loads(f.read_text(encoding="utf-8"))   # fails loudly on bad JSON, with the line number

    out = Path(a.out) if a.out else vm_env.workbench() / "pocket" / "set-preview" / name
    proj = out / "source"
    if proj.exists():
        shutil.rmtree(proj)
    shutil.copytree(KIT, proj, ignore=shutil.ignore_patterns(".hyperframes"))
    if data is not None:
        (proj / "sets").mkdir(exist_ok=True)
        (proj / "sets" / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")

    cams = (data or {}).get("cams", {})
    marks = (data or {}).get("marks", {})
    st = marks.get("stage", [0, 0, 8])
    cx, cz = st[0], st[2]
    wide = {"preset": "wide"} if "wide" in cams else {"from": [cx - 4, 13, cz + 58], "to": [cx + 2, 12, cz + 50], "look": [cx, 10, cz - 14], "fov": 36}
    views = [
        ("wide", wide),
        ("left", {"from": [cx - 30, 14, cz + 30], "to": [cx - 27, 13, cz + 27], "look": [cx + 8, 8, cz - 12], "fov": 40}),
        ("right", {"from": [cx + 30, 14, cz + 30], "to": [cx + 27, 13, cz + 27], "look": [cx - 8, 8, cz - 12], "fov": 40}),
        ("top", {"from": [cx, 78, cz + 14], "to": [cx, 74, cz + 12], "look": [cx, 0, cz - 4], "fov": 40}),
    ]
    cast = [{"who": "mani", "at": [cx - 4, 0, cz], "pose": "idle"}, {"who": "bit", "at": [cx + 4, 0, cz + 1], "pose": "idle"}] if a.cast else []
    shots = [{"id": v, "t0": i, "t1": i + 1, "set": name, "cam": cam, "focus": [cx, 6, cz], "lens": {"aperture": 0.35}, "cast": cast, "out": "cut"}
             for i, (v, cam) in enumerate(views)]
    (proj / "shots.js").write_text("window.SHOTS = " + json.dumps({"size": [1920, 1080], "duration": len(views), "shots": shots}, indent=1) + ";\n", encoding="utf-8")

    snaps = out / "stills"
    if snaps.exists():
        shutil.rmtree(snaps)
    times = ",".join(str(i + 0.5) for i in range(len(views)))
    npx = shutil.which("npx") or "npx"
    r = subprocess.run([npx, f"hyperframes@{vm_env.HF_VERSION}", "snapshot", "--at", times, "--no-end", "--describe", "false", "-o", str(snaps)],
                       cwd=proj, capture_output=True, text=True, shell=(sys.platform == "win32"))
    stills = sorted(snaps.glob("frame-*.png"))
    if len(stills) < len(views):
        print((r.stdout + r.stderr)[-1500:])
        raise SystemExit("snapshot failed: fix the set file (a JSON or prefab error shows above) and run again")
    print(f"stills:  {snaps}")
    print(f"sheet:   {snaps / 'contact-sheet.jpg'}")

    if a.concept:
        concept = Path(a.concept)
        side = out / "compare.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(concept), "-i", str(stills[0]), "-filter_complex",
                        "[0:v]scale=-2:720[a];[1:v]scale=-2:720[b];[a][b]hstack=inputs=2", "-frames:v", "1", str(side)], check=True)
        print(f"compare: {side}   (left = concept, right = wide render)")
        try:
            from PIL import Image
            def grid(p):
                im = Image.open(p).convert("RGB").resize((16, 9), Image.BOX)
                return [im.getpixel((x, y)) for y in range(9) for x in range(16)]
            def dominant(p):
                im = Image.open(p).convert("RGB").resize((96, 54)).quantize(6).convert("RGB")
                cols = sorted(im.getcolors(96 * 54), reverse=True)[:6]
                return ["#%02x%02x%02x" % c for _, c in cols]
            ga, gb = grid(concept), grid(stills[0])
            diff = sum(abs(x - y) for pa, pb in zip(ga, gb) for x, y in zip(pa, pb)) / (len(ga) * 3 * 255)
            la = sum(sum(p) for p in ga) / (len(ga) * 3 * 255)
            lb = sum(sum(p) for p in gb) / (len(gb) * 3 * 255)
            print(f"match:   colour difference {diff:.3f} (0 = identical; under 0.12 is close)")
            print(f"         brightness concept {la:.2f}, render {lb:.2f}")
            print(f"         concept colours {' '.join(dominant(concept))}")
            print(f"         render colours  {' '.join(dominant(stills[0]))}")
        except ImportError:
            print("match:   (install Pillow for the colour report)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

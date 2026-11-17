"""EXPERIMENTAL. A layered 3D world from ONE picture, no Blender, no GPU (HunyuanWorld's idea on a laptop).
Better: generate the layers separately with the image bridge (references/3d-worlds-without-blender.md, route 1).

    python world_build.py <picture.png | --prompt "..."> --name <world> -o <project>/source [--layers 3] [--fill cv|gen]

What it does (the HunyuanWorld idea, rebuilt for a CPU: picture -> depth -> semantic-ish layers -> meshes):
  1. the picture: yours, or made from --prompt with the ChatGPT image bridge (asset-first);
  2. depth with Depth Anything V2 (ONNX, CPU, vm_depth.py);
  3. splits it by depth into near / middle / far layers (quantiles; --layers 2..4), each a cut-out PNG with its own
     depth map, edges feathered and slightly grown so layers overlap instead of showing gaps;
  4. fills the far layer BEHIND the near layers: --fill cv (OpenCV inpainting, instant) or --fill gen (the image
     bridge repaints the scene without its foreground: a real clean plate, 4-6 min);
  5. places every layer at its own distance, scaled so the main camera sees the original picture exactly, each with
     its own relief, and writes source/sets/<world>.json (marks, a wide camera, the reliefs, a light).
The kit renders the layers as reliefs (`cutout` layers are alpha-tested), so the camera can move 2-3x further than
with a single relief plate before anything stretches: near things slide over a filled background.

Use in a shot: { set: "<world>", cam: { keys: [...] } }  (a dolly or crane of 40-70 voxels shows the depth).
Heavier route on a bigger machine: Apple SHARP (single image -> Gaussian splats, tools/ml-sharp) needs >= 16 GB RAM.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

S = Path(__file__).resolve().parent
sys.path.insert(0, str(S))
import vm_env  # noqa: E402

GEN = Path.home() / ".claude" / "skills" / "gpt-image-bridge" / "bin" / "gpt-image-2"


def sh(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise SystemExit((r.stderr or r.stdout)[-1500:])
    return r.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("picture", nargs="?")
    ap.add_argument("--prompt")
    ap.add_argument("--name", required=True)
    ap.add_argument("-o", "--source", required=True, help="the film's source/ folder")
    ap.add_argument("--layers", type=int, default=3, help="2: background + near; 3: background + ground + objects")
    ap.add_argument("--fill", choices=["cv", "gen"], default="cv")
    ap.add_argument("--far-z", type=float, default=-72)
    ap.add_argument("--view", type=float, default=115, help="distance from the far layer to the main camera")
    a = ap.parse_args()
    src = Path(a.source)
    wd = src / "assets" / "worlds" / a.name
    wd.mkdir(parents=True, exist_ok=True)
    bash = "bash"

    pic = wd / "picture.png"
    if a.prompt:
        sh([bash, GEN, a.prompt + " Wide establishing shot, clear foreground / middle ground / far background, each "
            "layer hazier than the last, open ground low in the centre for characters. No text.", pic, "--size", "1536x1024"])
    else:
        img0 = cv2.imread(str(a.picture), cv2.IMREAD_COLOR)
        cv2.imwrite(str(pic), img0)
    img = cv2.imread(str(pic), cv2.IMREAD_COLOR)
    H, W = img.shape[:2]

    # 2. depth (white = near)
    dpath = wd / "picture_depth.png"
    sh([sys.executable, S / "vm_depth.py", pic, "-o", dpath])
    dep = cv2.imread(str(dpath), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0
    dep = cv2.resize(dep, (W, H))

    # 3. object-aware layers (the HunyuanWorld idea): far background / ground / objects that pop out of the ground.
    #    An object is kept whole on its own nearly flat layer, the ground is smoothed, so nothing stretches inside a
    #    layer; every layer behind is filled where the layers in front of it were.
    d8 = (dep * 255).astype(np.uint8)
    sm = cv2.GaussianBlur(d8, (0, 0), 9)
    thr, _ = cv2.threshold(sm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    near = cv2.morphologyEx((sm >= thr).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    local = cv2.medianBlur(d8, 151 if min(H, W) > 300 else 31).astype(np.int16)
    obj = (((d8.astype(np.int16) - local) > 8) & (near > 0)).astype(np.uint8)
    obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    nlab, cc, stats, _ = cv2.connectedComponentsWithStats(obj)
    keep = np.zeros_like(obj)
    for c in range(1, nlab):
        if stats[c, cv2.CC_STAT_AREA] > 0.002 * H * W:
            keep[cc == c] = 1
    obj = keep
    if a.layers <= 2:                      # two layers: background + everything near (objects folded into the ground)
        obj = np.zeros_like(obj)

    def fill(base, hole):
        hole = cv2.dilate(hole * 255, np.ones((7, 7), np.uint8), iterations=3)
        small = cv2.resize(base, (W // 2, H // 2))
        msk = cv2.resize(hole, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
        f = cv2.resize(cv2.inpaint(small, msk, 9, cv2.INPAINT_TELEA), (W, H))
        return np.where(hole[..., None] > 0, f, base)

    if a.fill == "gen":
        clean = wd / "far_clean.png"
        sh([bash, S / "gpt_image_ref.sh", "Repaint the attached picture as the SAME place with every foreground and "
            "middle-ground object removed: only the far background (sky, horizon, far hills or walls) continued naturally "
            "across the whole frame, same light, same colours, same camera, photoreal. No text.", clean, "--ref", pic, "--size", "1536x1024"])
        far = cv2.resize(cv2.imread(str(clean), cv2.IMREAD_COLOR), (W, H))
    else:
        far = fill(img, near)
    ground = fill(img, obj) if obj.any() else img
    feather = lambda m: cv2.GaussianBlur(cv2.dilate(m * 255, np.ones((3, 3), np.uint8), iterations=2), (5, 5), 0)
    smooth = cv2.GaussianBlur(dep, (0, 0), 12)
    far_d = np.where(near > 0, float(np.percentile(dep[near == 0], 95)) if (near == 0).any() else 0.3, dep)
    plan = [("far", cv2.cvtColor(far, cv2.COLOR_BGR2BGRA), far_d, (near == 0)),
            ("ground", np.dstack([ground, feather(near)]), smooth, near > 0)]
    if obj.any():
        od = np.where(obj > 0, cv2.GaussianBlur(dep, (0, 0), 3), 0)
        plan.append(("objects", np.dstack([img, feather(obj)]), od, obj > 0))
    layers = []
    for i, (nm, rgba, ldep, region) in enumerate(plan):
        vals = ldep[region] if region.any() else ldep.ravel()
        lo, hi = float(np.percentile(vals, 2)), float(np.percentile(vals, 98))
        nd = np.clip((ldep - lo) / max(1e-3, hi - lo), 0, 1)
        if nm == "objects":
            nd = nd * 0.35                                       # objects nearly flat: they move as one piece
        cv2.imwrite(str(wd / f"layer{i}.png"), rgba)
        cv2.imwrite(str(wd / f"layer{i}_depth.png"), (cv2.GaussianBlur(nd, (0, 0), 2) * 255).astype(np.uint8))
        layers.append((i, nm, float(np.median(vals))))
    n = len(layers)

    # 4. place each layer at the distance of its median depth, scaled so the main camera sees the original picture
    cam_z = a.far_z + a.view
    w0, h0 = 186.0 * 1.12, 186.0 * 1.12 * H / W        # 12 % larger than the frame: edges never show
    dmin = layers[0][2]
    EYE = 12.0                                         # camera height: layers scale toward the eye, so they line up
    items = []
    for i, nm, md in layers:
        rel = 0.0 if i == 0 else min(0.85, max(0.15, (md - dmin) / max(1e-3, 1 - dmin)))
        D = a.view * (1 - 0.7 * rel)
        z = cam_z - D
        s = D / a.view
        amount = {"far": 40, "ground": 30, "objects": 10}[nm] * s + 6
        items.append({"relief": {"src": f"assets/worlds/{a.name}/layer{i}.png", "depth": f"assets/worlds/{a.name}/layer{i}_depth.png",
                                 "at": [0, round(EYE + (24 - EYE) * s, 2), round(z, 2)], "w": round(w0 * s, 2), "h": round(h0 * s, 2),
                                 "amount": round(amount, 1), "view": round(D, 1), "seg": 300,
                                 **({"cutout": True, "order": i + 1} if i > 0 else {})}})
    items.append({"prefab": "dust", "box": [-40, 0, -30, 80, 30, 60], "count": 120, "color": "#fff3c0"})
    items.append({"light": {"kind": "hemi", "color": "#fff3e0", "ground": "#3a3a3a", "intensity": 1.0}})
    st = {"name": a.name, "about": f"Layered world from one picture ({n} depth layers, fill={a.fill}), built by world_build.py.",
          "marks": {"stage": [0, 0, round(cam_z - a.view * 0.35, 1)]},
          "cams": {"wide": {"from": [-30, 12, round(cam_z, 1)], "to": [30, 14, round(cam_z - 20, 1)], "look": [0, 16, a.far_z], "fov": 40}},
          "castLight": {"key": "#fff3d6", "keySide": -1, "rim": "#ffe2a0", "rimSide": -1, "shade": 0.25}, "items": items}
    (src / "sets").mkdir(exist_ok=True)
    (src / "sets" / f"{a.name}.json").write_text(json.dumps(st, indent=1), encoding="utf-8")
    print(json.dumps({"world": a.name, "layers": n, "set": str(src / "sets" / f"{a.name}.json"), "camera_z": cam_z,
                      "try": f'{{ set: "{a.name}", cam: {{ keys: [{{ t: 0, from: [-30, 12, {cam_z:.0f}], look: [0, 16, {a.far_z:.0f}], fov: 40 }}, '
                             f'{{ t: 4, from: [30, 14, {cam_z - 20:.0f}], look: [0, 16, {a.far_z:.0f}], fov: 40 }}] }} }}'}, indent=1))


if __name__ == "__main__":
    main()

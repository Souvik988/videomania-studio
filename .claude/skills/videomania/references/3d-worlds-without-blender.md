# 3D worlds without Blender (research + what works on this machine, 2026-11-15)

The user asked for whole 3D environments built from pictures, no Blender. Researched on the web, GitHub and Reddit;
tested here (Ryzen 5600H, 7.4 GB RAM, Radeon RX 5500M, no CUDA).

## The field

| route | what | here? |
|---|---|---|
| HunyuanWorld 1.0 (Tencent) | text/image -> 360 panorama -> semantic layers -> layered meshes, explorable | no: CUDA only, large models |
| Apple SHARP (ml-sharp) | one image -> 3D Gaussian splats in under a second on a GPU; prediction also on CPU | installed (`<workbench>/tools/ml-sharp`), **runs out of memory on 7.4 GB** (needs ~4 GB free plus a 2.7 GB model); use on a 16 GB+ machine or a cloud GPU (ask first: it costs money) |
| Spark (sparkjs, in research/) | renders Gaussian splats in three.js | ready for SHARP's .ply when a machine can make them |
| img2threejs / Image Blaster | an agent decomposes a picture into three.js elements | research/img2threejs |
| relief plates (in the kit) | one picture pushed back along its depth map (Depth Anything ONNX, CPU) | **works**: moves up to ~30 voxels |
| layered generated plates | the image bridge makes a clean background and transparent objects; the kit stacks them at depths | **works, best quality** (asset-first; user rule 2026-11-13) |
| world_build.py (auto-split) | one picture -> depth -> far / ground / object layers, filled behind | **experimental**: parallax is real, but splitting a single photo by depth leaves seams and doubled edges on big moves |

## What to do (in order of quality)

1. **Generated layers (default for any world the camera travels through).** Ask the image bridge for the layers
   separately, in one style, same camera:
   - the far plate: "<place>, wide, NO foreground objects, open ground" (1536x1024) -> `vm_depth.py` -> a `relief`
     at the back of the set;
   - the ground or middle plate, if needed, as a second relief nearer;
   - each object as a transparent sticker (magenta-key sheet -> `pose_sheet.py`) -> sprites or `cutout` reliefs at
     their own distances (`{ "relief": { ..., "cutout": true, "order": 2 } }`).
   Camera moves of 40-70 voxels stay clean, because nothing is stretched: every layer is a whole picture.
2. **One picture, small moves (<= 30 voxels):** a single relief plate (`sets/meadow.json`, `sets/vista.json`).
3. **One picture, bigger moves, no time to generate layers:** `world_build.py <picture> --name <w> -o <source>`
   (add `--fill gen` so the image bridge repaints a clean background plate behind the near layers). Check every
   frame: seams and doubled edges show on swings over ~40 voxels.
4. **Gaussian splats:** SHARP on a machine with 16 GB+ RAM or a GPU, rendered with Spark; not on this laptop.

## Kit support added

`relief.cutout: true` (alpha-tested layer, `order` sets draw order) so layered worlds stack without stretching
between layers. `world_build.py` writes a set file that uses it.

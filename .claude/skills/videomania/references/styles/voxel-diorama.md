---
name: Voxel diorama with a pixel-art cast
description: One dark 3D voxel room the whole film lives in, pixel-art sprite characters who act the story, warm lamp light with shallow depth of field, word-by-word type with one red punch word, and pixel-dissolve transitions. For explainers, launches and creator videos that need a host.
tags: pixel, voxel, 3d, character, explainer, dark, cinematic, depth of field, kinetic type, mascot
---

# Voxel diorama with a pixel-art cast

Decoded on 2026-11-13 from one 120 s reference film (16:9, 2560×1440, 30 fps, about 125 visual changes).
This card is the **grammar**: how the look is built and timed. Never reuse the reference's characters,
name, script, UI text or layouts. Design a new cast and a new room for every brand.

## 1. What the viewer sees

- **One world.** A near-black room made of voxels (cubes): desk, lamp, monitor, keyboard, shelves with
  book spines, a rug, a plant. The film never leaves it for long; the camera moves to a new part of the
  room instead of cutting to a new background.
- **A cast of two.** A lead (human-like sprite, 32–48 px tall on its own grid) and a sidekick (a simple
  blocky creature, 16–24 px). They are flat pixel sprites standing in the 3D room, always facing the
  camera. They point at things, hold props, react. One of them is on screen for more than 60% of the film.
- **Real lens and light.** A warm practical light (the lamp) is the key. Everything far from the focus
  point is blurred; bright things bloom. Focus moves between the character and the prop being discussed.
- **Type has three jobs.** White grotesk = the sentence. Red condensed caps = the one punch word of the
  beat. An italic or pixel face = one accent per scene (a thought word, or a number). Words arrive on the
  voiceover's word times, 2–5 words visible at once, never a paragraph.
- **Pixel transitions.** Scenes change through blocks: a mosaic of red squares floods the frame and
  drains; a dot grid breaks up and blows away; the picture pixelates down to 8 px blocks and resolves
  into the next shot. The transition is made of the same thing as the cast.

## 2. Palette and light (roles, not fixed hexes)

| Role | Reference value | Rule |
|---|---|---|
| Ground | `#0b0605` to `#1a0c0a` | 60–70% of every frame stays near-black |
| Voice | red `#e11d2e`, orange `#ff6a1a` | punch words, rug, lamp glow, transitions |
| Cool accent | teal `#19c8b9` | one use per scene: a UI edge, a floor grid, a number |
| Type | `#ffffff`, 88% for secondary | never coloured except the punch word |
| Key light | warm `#ffb057`, from the lamp | one visible source; the room falls off to black |
| Rim | red or teal, low | separates the cast from the dark |

Depth of field: focus on the speaking character; blur radius grows with distance; foreground objects may
be fully soft. Bloom only on emissive things (lamp, screen, punch word). Light vignette. Fine grain.

## 2b. Detail, depth and 3D type (user notes, 2026-11-13)

- **Fine pixels.** Big squares read as cheap. Sprites are drawn at 60 px tall or more on their own grid,
  with a shade tone, a highlight and rounded corners on every part. Set detail is at half-voxel scale:
  thin planks, book spines, cables, small props. In a medium shot no sprite pixel is larger than about
  12 screen pixels at 1080p.
- **Depth in layers.** Every shot has a foreground (soft, close to the lens), the subject, a middle
  ground and a far distance. When the camera moves, near things cross the frame faster than far things.
- **2.5D plates.** A set can be built the way a 2D game builds parallax: flat art plates at different
  depths (`plates` in the shot list, or a layered set such as `city-night`). Plates are drawn in code or
  generated with ChatGPT as transparent layers in one style. At least four depths.
- **Kinetic 3D type.** Hero words can stand in the world as extruded letters (`type3d`): they slam in,
  swing or rise on their spoken time, take the lens blur and are passed by the camera. Use it for the
  punch word or a number; keep sentences in the flat type layer.
- **Clean.** One clear subject per shot, empty space around it, few colours, no clutter in front of faces.

## 3. Shot grammar

| Shot | Use it for | Camera |
|---|---|---|
| Hero medium | a character says the line | slow push-in 3–5% over the shot |
| Over-the-desk wide | establishing, "here is the setup" | slow orbit 8–15° |
| Top-down | a process, a layout, "everything on the table" | slight rotate |
| Into the monitor | showing a UI, a file, a timeline | whip push through the screen edge, match cut |
| Prop close-up | "this file", "this skill" | rack focus from character to prop |
| Type-only on black | a hard statement, a number | type moves, one small sprite in a corner keeps continuity |
| Metaphor insert | scale or drama (space, storm) | 1.5–3 s, monochrome, no more than 3 per film |
| Card fan / board | "6 versions", "4 parts", progress | cards deal out on a curve; bars fill with voxel texture |

Rules measured from the reference:

- Shot length 2–4 s. A dense run of 4–6 shots is followed by one 3 s hold.
- The camera is moving at every cut (in and out), so cuts join motion to motion.
- Every number gets its own beat in a pixel or 7-segment face and counts up to its value.
- Icons for a list (script, storyboard, animation, captions, voice) appear as rounded dark cards with a
  label, one per spoken item, and the lead walks past them.
- The end card holds 6–8 s: lead and sidekick on the left third, a typed call to action on the right.

## 4. Pixel transitions (recipes)

1. **Mosaic flood.** A grid of 60–120 px squares in 3 reds fills from a corner in 8 frames, holds 4,
   drains toward the opposite corner in 8. Cut under the full frame.
2. **Dot break-up.** The frame becomes a grid of rounded squares that scale to 0 from one side, with a
   cluster flying off as particles. 12–16 frames.
3. **Pixelate resolve.** Block size 2 → 64 px over 6 frames on the outgoing shot, cut, 64 → 1 px over 8
   frames on the incoming shot. This is also the **pixel switch** for live footage.
4. **Blur whip.** Directional blur + 120% translate over 5 frames; type smears with it.

## 5. Build route (kit: `templates/voxel-diorama/`, on HyperFrames with Three.js)

- The kit provides the voxel room builder, sprite billboards from a pixel grid, the lamp and rim lights,
  depth of field, bloom, grain, the four transitions, the three type roles and a camera rig.
- The director writes a **shot list** (`shots.json`): for each shot the location in the room, who is
  there and their pose, the camera move, the words with their times and which word is the punch word,
  and the transition out. The kit renders it. Custom shots are added as code only when the list cannot
  express them.
- Cast: design each sprite on a grid (text rows of palette indices) in 3–5 poses: idle, talk, point,
  cheer, think. A reference picture from ChatGPT may be snapped to the grid and palette, then cleaned by
  hand. Outline every part separately with a 1 px dark edge so limbs read.
- Seek-safe: every animated value is a pure function of time; no free-running loops.

## 6. Checks before showing a draft

- A character is visible in more than 60% of frames.
- No shot shorter than 0.8 s or longer than 5 s, except the end card.
- At most 5 words on screen at once; exactly one punch word per beat; the punch word is on its spoken time
  within 2 frames.
- Ground stays dark: mean luma under 0.25 outside transitions and inserts.
- The camera never rests for more than 1.5 s.
- Each transition type is used at least once, and no single type more than half the time.
- Template lint (`scripts/template_lint.py`) and the standard QA and critic passes.

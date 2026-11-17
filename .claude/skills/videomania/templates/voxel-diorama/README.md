# Voxel-diorama kit

A dark 3D voxel room, a pixel-art cast, lamp light with depth of field, three type roles and pixel
transitions, driven by one file: **`shots.js`**. You direct; the kit draws. Style rules:
`references/styles/voxel-diorama.md`.

Runs on HyperFrames with Three.js (vendored, no network). Every frame is a pure function of time.

## Make a film

1. Copy this folder to `projects/<id>/source/`.
2. Write `shots.js` from the storyboard (`storyboard/shots.json` has the same fields). Times are
   seconds from the start of the film, taken from the voiceover's word times.
3. Add the sound: `scripts/sound_mix.py` writes the finished mix to `source/mix.wav`; put
   `<audio id="mix" src="mix.wav" data-start="0" data-duration="<film length>" data-volume="1"></audio>`
   inside `#root` in `index.html`, and make `#root`'s `data-duration` the same length.
4. `npx hyperframes check` (must pass), `npx hyperframes snapshot --at <times>` (look at the frames),
   then `npx hyperframes render -o ../renders/draft.mp4`.

A 20 s 1080p film renders in a few minutes on a laptop GPU.

## shots.js

```js
window.SHOTS = {
  size: [1920, 1080],            // or [1080, 1920]
  duration: 20,
  palette: { voice: "#e11d2e", voice2: "#ff6a1a", accent: "#19c8b9" },   // punch words and transitions, numbers, the one cool accent
  lens: { aperture: 0.9, maxBlur: 15, glow: 0.55, exposure: 1.7 },      // optional
  sets: { studio: { rug: "#c8121f" } },                                 // optional set options
  shots: [ /* one object per shot, in order, no gaps */ ],
};
```

### A shot

| Field | Meaning |
|---|---|
| `id`, `t0`, `t1` | name, start and end in seconds. 2–4 s is normal; 0.8 s minimum |
| `set` | `"studio"` (the room, with a night city behind its window), `"city-night"` (a street built only from flat layers), or `"void"` (black with a teal floor grid, for hard statements and numbers) |
| `cam` | `{ preset, on }` plus optional overrides `from`, `to`, `look`, `lookTo`, `fov`, `fovTo`, `up` (arrays in voxels) |
| `focus` | what is sharp: a cast name, `"screen"`, `"desk"`, `"prop:<id>"`, `"card:<id>"`, `[x,y,z]`, or `{ from, to }` for a rack focus |
| `cast` | `[{ who, at, pose, flip, enter, say }]` |
| `screen` | what the monitor shows: `{ kind: "chat", title, lines:[text] }`, `{ kind: "code", lines:[...] }`, `{ kind: "timeline" }` |
| `cards` | floating icon cards: `[{ id, label, icon, at:[x,y,z], t, color }]`; icons `doc board play cc mic bulb` |
| `props` | `[{ id, kind:"doc", at:[x,y,z], t, scale, color }]` |
| `type` | where the words sit: `{ x, y, w, align, size }` as fractions of the frame |
| `lines` | the flat words (below) |
| `type3d` | words that stand in the world as extruded letters (below) |
| `lens` | per-shot lens override, e.g. `{ aperture: 0.4 }` to keep a far skyline readable |
| `out` | transition into the next shot: `"cut"`, `"mosaic"`, `"dots"`, `"pixelate"`, `"whip"` |

### Camera presets

| Preset | Use |
|---|---|
| `hero-push` | a character says the line; slow push-in on `on` |
| `hero-orbit` | the same subject with a slow arc |
| `low-hero` | a low angle, for a strong claim |
| `two-shot` | both characters on the stage |
| `dolly` | a sideways move past the subject (`dir: "left"` reverses it): the clearest way to show depth, because near layers cross the frame faster than far ones |
| `wide-orbit` | the whole room; openings |
| `top-down` | the desk from above; processes |
| `monitor-push` | fly into the monitor; pair with `screen` and `focus: "screen"` |
| `prop-rack` | a prop or card with `focus: { from: "mani", to: "prop:<id>" }` |
| `void-centre` | the subject in the void set |

The camera never stops inside a shot and is still moving at both cuts.

### Cast

| Who | Poses | Notes |
|---|---|---|
| `mani` (the host, 60×68 px) | `idle talk point cheer think` | `talk` moves the mouth; `say: [t0, t1]` limits it to those seconds |
| `bit` (the sidekick robot) | `idle talk happy jump` | |

`at` is a mark (`stage`, `stage-left`, `stage-right`, `stage-front`, `desk-left`, `desk-right`, `centre`,
`centre-left`, `centre-right`) or `[x, y, z]`. `flip: true` mirrors the sprite. `enter: "hop"` hops in.

New characters: add a drawer to `kit/cast.js`: block the parts in, then add a shade tone, a highlight and
rounded corners in fine pixels, then `outline()`. At least 60 px tall, 3–5 poses, listed in `CAST`. Design your own; never trace an existing character.

### Words

`lines` is a list of groups. A group replaces the one before it at its first word's time. A word is
`[text, time, role]`; `["\n"]` breaks the line.

| Role | Look | Rule |
|---|---|---|
| (none) = say | white grotesk | the sentence |
| `punch` | big red condensed caps | exactly one per beat, on its spoken time |
| `accent` | italic serif | at most one per shot |
| `num` | orange pixel digits, counts up | every number gets its own beat |
| `soft` | small secondary line | credits, a call to action |

Keep at most 5 words visible at once.

### 3D words (`type3d`)

`type3d: [{ text, t, at: [x, y, z], size, anim, ry, role, color, depth }]`. The word is built as a stack of
flat copies, so it reads as a solid block, takes the lens blur and is passed by the camera.

| Field | Meaning |
|---|---|
| `at`, `size` | centre of the word in voxels, and its height in voxels (5–7 reads well in a two-shot) |
| `anim` | `slam` (flies in from the lens and lands), `swing` (turns in like a door), `rise` (tips up from the floor), `drop` |
| `role` | `punch` (default: red condensed caps), `say`, `accent`, `num` |
| `ry` | turn in radians; aim it at the camera's side of the room |

Use it for the punch word or a number, at most one per shot. Check a snapshot: a word placed outside the
camera's view or behind the cast is the usual mistake.

### Moves

Every trick is a named move with a job. The catalogue (39 moves with "use when") is `engines/moves.json`;
search it with `python scripts/pocket.py search "<the beat's job>" --kind move`.

| Kind | Moves | How |
|---|---|---|
| Word effects | marker box, coloured letters, typed text, corner brackets | a fourth item on a word: `["effects.", t, "say", "mark"]` with `mark`, `jitter`, `type` or `bracket` |
| 3D words | slam, swing, rise, drop, **through the lens** | `type3d: [{ text, t, at, size, anim }]` (`through`: start far away, e.g. `at: [0, 9, -40]`) |
| On screen | sticker burst, typed search bar, level bar, cursor that clicks | `burst: [{ t, x, y, n, kinds }]`, `search: { text, t: [a, b], x, y, w }`, `meter: { label, value, t, x, y }`, `cursor: { from, to, t: [a, b] }` (x and y are fractions of the frame) |
| In the world | card fan, film strip, icon cards, document | `fan: { t, at, labels }`, `strip: { t: [a, b], at, count }`, `cards`, `props` |
| Transitions | `flash`, `iris`, `mosaic`, `dots`, `pixelate`, `whip`, `cut` | `out: "flash"` |
| Camera | `crane`, `pull-back`, `push-through`, `dutch`, `ots`, `vertigo`, `snap-zoom` (+ `snap: { t, fov }`), `shake: 1` on any camera | `cam: { preset, on }` |

Rules: pick a move for its job, at most two different moves in a shot, no move more than three times in
a film, and check a snapshot (a fan or a 3D word placed outside the camera's view is the usual mistake).

### Transitions

`mosaic` red blocks flood and drain · `dots` an orange dot grid sweeps · `pixelate` the picture breaks
into blocks and resolves (also the pixel switch for footage) · `whip` a blur whip · `cut`. Use at least
two kinds in a film and none for more than half the cuts.

## Depth: layers front to back

Every shot should have four depths: something soft near the lens, the subject, a middle ground, and a far
distance. The kit gives you these:

- **Near:** string lights and dust between the lens and the stage (they turn into soft orbs), crates, the railing in `city-night`.
- **Middle:** the desk, lamp, plant, shelves.
- **Far:** the night city behind the studio window, in three flat layers at different depths, and the whole of `city-night`.
- **Your own plates.** Flat art generated with ChatGPT (transparent PNG layers in one style) or drawn elsewhere:
  `plates: [{ set: "studio", src: "assets/plates/hills.png", at: [0, 14, -70], w: 160, h: 60, glow: 1.2 }]` at the
  top level of `SHOTS`. Put near plates at small negative z and far ones at large negative z, then use a
  `dolly` or an orbit so they slide at different speeds.

## Sets as data (no code, no Blender)

A set is one file: `sets/<name>.json`. Name it in a shot (`set: "cafe"`) and the kit loads it. The file
lists prefabs (`table`, `counter`, `shelf`, `pendant`, `plant`, `city`…), plain boxes, flat plates and
lights, plus the set's own `marks` (where the cast stands) and `cams` (its camera presets, such as
`wide`). The format and every prefab are documented at the top of `kit/setdata.js`; `sets/cafe.json` is a
finished example rebuilt from a ChatGPT concept picture.

Build one with crew job 4b (`crew/04b-set-builder.md`):
`python scripts/set_preview.py --set <name> --cast --concept <picture>` renders four views and a
side-by-side with the concept, with a colour-difference score.

### A world from one picture (relief plates)

Any generated picture can become a backdrop with real camera depth:

1. Generate the picture (ChatGPT image bridge). Ask for clear near, middle and far layers, each hazier
   than the last, and open space low in the centre where the cast will stand.
2. `python scripts/vm_depth.py assets/plates/<name>.png` writes `<name>_depth.png` on this machine (CPU,
   about 100 MB model, a few seconds). It prints how much of the picture is near and far.
3. Use it as a `relief` in a set file (see `sets/vista.json`) or in `SHOTS.plates` (add `depth`):
   `{ "relief": { "src": "...png", "depth": "..._depth.png", "at": [0, 24, -72], "w": 186, "h": 124, "amount": 58, "view": 115 } }`
   - `w`, `h`: a little larger than the frame at that distance (at 115 voxels and a 40° lens the frame is about 150 × 84).
   - `amount`: how far the nearest parts come forward, in voxels. 40–60 gives clear parallax; more starts to stretch edges.
   - `view`: distance from the plate to the main camera, so the picture looks unchanged from there.
4. Move the camera sideways or up (`dolly`, or a set camera whose `from` and `to` differ by 20–30
   voxels). Keep moves under about 30 voxels: beyond that the stretched edges behind near objects show.

`vista` is a ready set: a rock ledge in front of a relief plate. Swap its two pictures for any world.

### Actions: a cast that acts

Give a cast member `acts`: a list of actions in order, each with its own seconds `t: [start, end]`. The
position carries from one action to the next, and frames stay exact (every action is a pure function of time).

```js
{ who: "mani", at: [-30, 0, 14], acts: [
    { do: "run",  to: [0, 0, 10], t: [0.2, 2.2] },
    { do: "jump", height: 5, t: [2.6, 3.4] },
    { do: "fly",  path: [[-12, 16, 4], [6, 20, 0], [8, 9, 10]], t: [4, 8] },
    { do: "fly",  to: [-4, 0, 8], t: [8, 9] },          // come down: the landing squash is automatic
    { do: "wave", t: [9.4, 12], hold: true } ] }
```

| Action | Fields | What happens |
|---|---|---|
| `walk`, `run` | `to` | step cycle along the ground, facing the way they go; `run` is faster and leans |
| `jump` | `height`, `to` (optional) | crouch, arc with stretch, land with a squash |
| `fly` | `to` or `path: [points]` | a smooth curve through the points, head first in the direction of travel, with a light trail; landing squash at the end |
| `land` | | squash and settle in place |
| `sit`, `wave`, `pose` | `pose`, `hold: true` to keep it after `t` ends | hold a pose (`pose` takes any pose name) |

`to` and `walk` directly on the cast entry are the short form of one walk. Keep jumps under about a
third of the frame height for the camera in use, and check a snapshot at the top of every jump and flight.

Poses: `mani` has `idle talk point cheer think walk fly sit wave jump`; `bit` has `idle talk happy jump walk fly`.

### Sprites are lit by the room

Every sprite is darker on the side away from the set's key light, picks up a little of the key colour on
the lit side, and gets a rim of light along its edge on the rim side. A set file can set this with
`"castLight": { "key": "#ffb057", "keySide": -1, "rim": "#19c8b9", "rimSide": 1, "shade": 0.3 }`
(−1 = from the left, 1 = from the right).

### A new cast member from one picture

1. Generate the character with the ChatGPT image bridge: one character, full body, facing the viewer, crisp
   pixel art about 64 px tall with a dark outline, on a flat pure magenta (#FF00FF) background, nothing else.
2. `python scripts/sprite_import.py <picture> -o assets/cast/<name>.png --tall 64 --outline` removes the
   background, snaps it to a real pixel grid, limits the palette and writes a preview. Look at the preview.
3. In `shots.js`: `cast: { fox: { src: "assets/cast/fox.png", tall: 8.5 } }` at the top level (`tall` = height in
   voxels; the host is about 12). Then use `who: "fox"` in any shot. One picture serves every pose; all
   actions still move it (it waddles when it walks).
4. For extra frames or hand clean-up, open the PNG in Aseprite
   (`<workbench>/tools/aseprite/build/bin/aseprite.exe`). Original characters only.

### Film length

Set `duration` in `shots.js` **and** `data-duration` on `#root` in `index.html` to the same number.

## Sets (built in)

`kit/sets.js`: a set is a function that fills a collector with `box()`, `vox()` (use `unit: 0.5` for fine
detail), `plate()` (a flat art layer drawn on a canvas) and `light()`. Keep detail fine: big squares read as
cheap. Add a set (a workshop, a spaceship, a forest) as another function and list it in `SETS`; add its
named places to `MARKS` (studio: `stage…`, `desk…`, `window`; street: `street`, `street-left`, `street-right`).

## What the kit guarantees, and what you must still check

Guaranteed: seek-safe frames, depth of field and bloom from one pass, text contrast on dark, cast always
facing the camera, transitions centred on the cut.

Check on real frames: the cast is not hidden behind type, each punch word lands on its spoken time, a
character is on screen for more than 60% of the film, and `template_lint.py` passes.

## Rhythm fields (2026-11-14) — change inside the take

Read `references/rhythm-and-direction.md` first. Fields on a shot:

| field | example | what it does |
|---|---|---|
| `cam.keys` | `[{t, from:[x,y,z], look:[x,y,z], fov, up}]` | keyframed camera path, Catmull-Rom between keys; one long take that moves on the words |
| `flicker` | `{ t: [0, 0.6], looks: ["negative","red","mono","normal"] }` | look burst (1 negative, 2 red silhouette, 3 mono); on shot 0 it replaces the fade-in |
| `wash` | `[{ t: 5.74, color: "#e11d2e", k: 0.6, dur: 0.5 }]` | a colour wash over the frame instead of a cut |
| `type.compose` | `type: { compose: true, ink, punch, flicker }` | every word placed on its own: 5th tuple element `C(x, y, {size, rot, tilt, skew, arc})` |
| word fx | `"jitter"`, `"type"`, `"mark"`, `"bracket"` | letters drop in, typed, marker box, corner brackets (mark/bracket combine with letter flicker) |
| `type.flicker` | `false` | turn off the default colour flicker of letters (bright sets) |
| cast `dissolve` | `[13.85, 15.0]` | pixel dissolve out and re-form (0.48 s) — use on pose changes and entrances |
| `lens` | `{ aperture: 0.38, maxBlur: 9 }` | defaults are sharp; raise only when blur is motivated |

Helper for word places, at the top of `shots.js`: `const C = (x, y, o = {}) => Object.assign({ x, y }, o);`

## Picture mascots, depth type, image screens (2026-11-14)

| field | example | what it does |
|---|---|---|
| `SHOTS.cast.<who>.poses` | `{ poses: "assets/mascot/me/poses.json", tall: 12.5, ref: "talk" }` | a mascot made of pictures, one per pose (from `scripts/pose_sheet.py`); breathes, talks, steps; missing poses fall back |
| cast `acts` poses | `{ do: "pose", pose: "sit_code", t: [16.6, 18.8] }` | any pose name in poses.json: talk point walk jump sit_code think cheer wave run floor_code shrug fly hold_doc surprised holo_type thumbs idle |
| `type.depth` | `type: { compose: true, depth: true }` | 3D typography: words fly in from depth, drift, the old group recedes |
| word place `from`, `z` | `C(0.3, 0.5, { from: "near", z: -200 })` | entrance from `deep`, `near` (behind the lens) or `side`; own depth in px |
| `screen.kind: "image"` | `{ kind: "image", src, crop: [x,y,w,h], zoom: 0.18, at: [0.5, 0.15] }` | a generated picture on the monitor, slow push |
| `SHOTS.plates` | `[{ set, src, at, w, h, glow }]` | a generated backdrop behind a set (sunburst wall on color-studio) |
| set `meadow` | `sets/meadow.json` | photoreal relief world for real-world openings (needs `assets/plates/open_world.png` + `_depth.png`) |
| `lens.sat`, `lens.contrast`, shot `grade` | `sat: 1.22, contrast: 1.1` | crisp saturated grade |

Worked example: `examples/director-film-v5.shots.js` (23 chapters, mascot acting, real-to-pixel opening) and `examples/director-film-v5.score.sh` (song entrances, a cappella spans, a literal dip). Older versions: `examples/history/`.

## Real assets, footage on screens, doodles, 2.5D mascots (2026-11-14, v4)

| field | example | what it does |
|---|---|---|
| card `img` | `{ id: "a", label: "Script", img: "assets/gen/icons/script.png", at, t, scale: 0.85 }` | a generated icon is the card |
| `screen.kind: "frames"` | `{ kind: "frames", src: "assets/clips/this_video/f_%03d.jpg", count: 74, title: "this_video.mp4" }` | real footage plays on the monitor across the shot (title bar + progress bar) |
| `fan.imgs`, `strip.imgs` | `fan: { labels: ["v1"...], imgs: ["assets/clips/versions/v1.jpg", ...] }` | real frames dealt as cards |
| `doodles` (OFF for this user: they asked to remove them in v5; use only when asked) | `[{ kind: "x", on: "card:course", t, dur: 0.35, w: 0.13, h: 0.24, width: 1.3, hold: 1 }]` | hand-drawn marker strokes that draw on: circle, underline, x, arrow (`to: [x,y]`), check, star, scribble; anchored to the frame (`x, y`) or to a thing (`on: "card:<id>"`, `"me"`, `[x,y,z]`) |
| mascot depth | poses.json `depth` (from `scripts/pose_depth.py`), cast `lift: 0.9`, `flat: true` | 2.5D relief: displaced toward the camera and lit from the depth normals |
| shot `drawn_ok` | `drawn_ok: "slop is meant to look generic"` | lets the brain gate pass a deliberately code-drawn element |

Worked example: `examples/director-film-v5.*` (v4 with doodles is in `examples/history/`; the user removed doodles in v5).

## Reel / portrait mode (2026-11-14, v6 reel)

The kit renders any size; `size` with height > width switches on portrait mode: the camera keeps
`portraitKeep` of the landscape width and opens up vertically, words and overlays (search bar, meter) move
into the taller frame, and type is sized from the width.

| field | example | what it does |
|---|---|---|
| `size` | `[1080, 1350]` (4:5) or `[1080, 1920]` (9:16) | the page size; `index.html` viewport, `#root` data-width/height and the canvas must match |
| `portraitKeep` | `0.82` for 4:5, `0.62` for 9:16 | share of the landscape width the camera keeps |

**The user's reel format** ("9:16, the video attached in the middle, black top and bottom, not transformed
totally into 9:16"): compose at 4:5 and pad to 9:16. Never a 16:9 strip in a 9:16 frame (too thin) and never a
full native 9:16 re-composition (not wanted).

```bash
python $S/reel_frame.py prep source --size 1080x1350 --keep 0.82   # page + shots.js to 4:5 (backs up the landscape files)
npx hyperframes snapshot --at <busy moments> --no-end --describe false -o ../snaps_reel   # move any card now outside the frame
npx hyperframes render -o ../renders/<film>_4x5.mp4
python $S/reel_frame.py pad ../renders/<film>_4x5.mp4 ../renders/<film>_reel_9x16.mp4
python $S/reel_frame.py restore source                             # back to the landscape page and shots
```

Worked example: `examples/director-film-v5-reel4x5.shots.js` (two lines differ from the 16:9 film).

## Starting a film (2026-11-14)

`python scripts/new_film.py <project> --duration <s> [--assets-from <earlier project>]` does the setup (kit copy, page size,
audio tag, skeleton `shots.js`, asset folders, reuse of the approved mascot/icons/screens/backdrop). The cast table
above lists the built-in `mani`/`bit`; the creator's picture mascot is `me` (`SHOTS.cast.me.poses`, 17 poses incl.
`sit_code floor_code holo_type hold_doc thumbs fly`). `scripts/split_frames.py` makes the two-worlds split monitor.
Worked 10 s clip: `examples/clip10-short.shots.js` + `.score.sh`.

## Frame 0 (2026-11-15)
The kit no longer fades in from black: frame 0 is the full picture (the hook). `SHOTS.fadeIn: true` brings the old
0.25 s fade back only when the user asks. The editor effects (glitch, warp, shake, flashes ...) and hook sounds are a
separate pass on the rendered film: `scripts/fx_pass.py`.

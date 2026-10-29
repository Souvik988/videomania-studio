# Motion kit: build every film from tested parts, not one-off code

`assets/motion-kit/` is Video Mania's motion toolkit for HyperFrames. `scripts/new_composition.py`
copies it into each film's `source/`. It exists because hand-written motion in an 800-line file is
where films turn generic: each film re-invents springs, morphs and reveals slightly worse. Use the
kit and the installed libraries first; write custom code only for the film's signature idea.

## What to reach for, in order

| Need | Use | Where |
|---|---|---|
| a whole shot's choreography (hook, product intro, benefits, CTA…) | one of **22 blueprints** mined from 178 launch clips | `hyperframes-animation/blueprints-index.md` → `blueprints/<id>.md` |
| an atomic move (ticker, glitch, gradient sweep, counting scale, camera flight, card morph anchor, spring pop, cursor drag, path draw, motion-blur streak, …) | one of **48 rules**; compose 2–4 per scene | `hyperframes-animation/rules-index.md` → `rules/<name>.md` |
| a premium effect (one object changing shape) | **`MKFX.*`** (below), from the 16 effect recipes | `assets/motion-kit/motion-fx.js`; recipe text via `motion_refs.py --effect` |
| springs, morphs with a ghost, camera windows, spotlight, mask reveals, count-up, typing, iris/keyhole, particles, grain, captions | **`MK.*`** (below) | `assets/motion-kit/motion-kit.js` |
| a ready layout for a stat, list, section card, lower third | a **card donor** (restyle it) | `motion_refs.py --cards "<purpose>"` |
| a transition between two scenes | the transition catalogue, or a bridge from the motion brief | `hyperframes-animation/transitions/catalog.md`, playbook §2 |
| 3D, Lottie, shaders, WebGPU | a runtime adapter | `hyperframes-animation/adapters/{three,lottie,html-in-canvas-patterns,typegpu}.md` |
| a block to drop in (447 registry items) | registry, restyled | `/hyperframes-registry` |
| design direction (palette, frame presets, story spine) | design picker | `hyperframes-creative/references/{design-picker,story-spine,beat-direction,visual-styles}.md` |

## Scaffold (`templates/composition/index.html` via `new_composition.py`)

- One paused GSAP timeline. Everything is built inside `async build()` **after fonts load**, so
  text is split, measured and rasterised in the right face, and frame 0 never paints a fallback.
  HyperFrames waits for `window.__timelines.main` (verified on the gallery).
- `scene(id, start, end, (s, t0) => {...})` shows a scene in its window (seek-safe sets). Overlap
  windows to build bridges.
- Captions come from `data.js` (`caption_track.py --mode chunk|phrase`) through `MK.captions`. One
  box style for the whole film, with a thin light edge. `window.CAP_OFF` holds the windows where a
  headline spells the words.
- Grain is re-seeded every frame through the timeline. `MK.pad` keeps the slot filled.
- Look tokens (`--mk-*`) are inlined from `assets/motion-kit/looks/<look>.css` (warm-editorial,
  apple-product, dark-lit, minimal-dimensional), plus `brands/<slug>/tokens.css` when `--brand`
  is given.

## `MK` toolkit (motion-kit.js)

| Helper | What it does |
|---|---|
| `MK.spring({stiffness, damping})` | analytic damped spring → `{ease, duration, overshoot}`; presets: tight UI 260/24 (0.48 s, 3 %), soft card 170/18 (0.73 s, 5 %), playful 200/12 (23 %) |
| `MK.ease.glide / enter / exit / move` | signature curves; `MK.bezier(x1,y1,x2,y2)` for your own |
| `MK.maskRise(tl, el, at, {by})` / `MK.maskFall` | text rises through a cut line (words/chars/lines); exits faster than entrances |
| `MK.wordCarrier(tl, els, times)` | first word slides 360 px, tail decays 120→12 px; picture leads the word by 60 ms |
| `MK.morph(tl, shell, from, to, at, dur, {ghost, contents, oldContents})` | one object changing shape via clip-path (no width/height tweens); dashed ghost at the start; contents wait for room |
| `MK.camera(tl, world, frame)` → `.set(win, t)`, `.to(win, t, dur)`, `.durationFor(win)` | camera through one persistent world using exact windows |
| `MK.spotlight(tl, items)` → `.at(t, active, context)` | one element bright, context ~0.56, spent ~0.33 |
| `MK.countUp(tl, el, from, to, at, dur, {format})` | count-up with intl or Indian grouping (`₹50,000`, `12,34,567`) |
| `MK.drawPath(tl, path, at, dur)` | stroke draw-on |
| `MK.typeText(tl, el, text, at, dur, {caret})` | typing, only inside input boxes |
| `MK.iris(tl, el, {cx, cy, r0, r1, shape}, at, dur)` | circle or keyhole reveal (look-through bridges) |
| `MK.brackets(tl, parent, box, at)` | accent corner brackets saying "this one" before a lift |
| `MK.particlesTo(tl, parent, targets, at, {seed})` | seeded particles flying on arcs into points |
| `MK.grain(tl, parent, dur)` · `MK.captions(tl, el, cues, {off})` · `MK.bracketVideo` · `MK.pad` | finish, captions, video poster and last-frame bracketing, slot padding |
| `MK.rng(seed)` · `MK.hash(i)` · `MK.snap(t, fps)` · `MK.fitWindow` · `MK.formatNumber` · `MK.wordAt(words, text, near)` | deterministic utilities; `wordAt` anchors a move to a spoken word |

## `MKFX` effects (motion-fx.js)

Every effect reads `--mk-*` tokens and lands its move at `at` (the spoken word). Each keeps one
thing alive in its hold and returns handles that the next scene can use as a bridge.

| Effect | Story job |
|---|---|
| `MKFX.headline(tl, parent, at, {x,y,w,lines,size,accentWord})` | headline rising through mask lines, with an accent underline drawn under one word |
| `MKFX.chartMorph(..., {values, labels, tag, sample})` | bars become a line through their own tops; the same numbers; "example" chip for samples |
| `MKFX.dashboardZoom(..., {tiles, pick, card, title, value, delta})` | brackets, the rest dims, the tile lifts from its exact slot into a big card; guides from corner to corner |
| `MKFX.cardToWorkspace(..., {from, to, title, body})` | a card grows into a window; the title is a shared element; a ghost stays at the origin |
| `MKFX.springStack(..., {cards})` | cards fan out on springs with per-card damping; a ghost shows the resting angle |
| `MKFX.flowingPaths(..., {source, channels, result})` | pulses draw the connectors; nodes answer with rings; a second wave keeps the hold alive |
| `MKFX.counterTag(..., {to, format, label})` | a tag on a string swings in; the number rolls up and punches on the word |
| `MKFX.notifications(tl, parent, times, {items})` | notifications slide in on springs, newest on top, pushing the stack down |
| `MKFX.cursorClick(tl, parent, from, to, at, {target})` | cursor glide, click ripple and a press on the target |
| `MKFX.irisPass(tl, layer, at, {cx, cy, shape})` | keyhole or iris bridge into the next layer |
| `MKFX.particleWord(..., {text, font, color})` | seeded dots fly in and form a word (rasterised after fonts load) |

## Look book and tests

- **Gallery** (every effect plus camera and spotlight, 34 s, 9:16): `new_composition.py --project
  mk-gallery --look <look> --format 9:16 --duration 34 --scenes-js assets/motion-kit/gallery.scenes.js
  --gallery --force`, then `npx hyperframes snapshot` to see any effect in any look before choosing.
- **Maths tests:** `node assets/motion-kit/motion-kit.test.cjs` (springs, bezier, determinism, camera
  fit, number grouping).
- **Choreography audit:** `HYPERFRAMES_SKILL_BOOTSTRAP_DEPS=1 HYPERFRAMES_SKILL_PKG_VERSION=0.8.162 node
  ~/.claude/skills/hyperframes-animation/scripts/animation-map.mjs source --out qa/anim-map`. It
  reports dead zones, stagger rhythm, density and offscreen or degenerate tweens. Designed overlaps
  show as "collision"; judge them on frames.

## Rules of use

- Variety (hyperframes-animation motion principles):
  - no more than 2 independent tweens with the same ease in a scene;
  - the slowest scene about 3× slower than the fastest;
  - vary entry directions;
  - each scene has its own stagger rhythm;
  - offset the first move 0.1–0.3 s.
- Build, breathe, resolve within every scene; exits are faster than entrances.
- Effects are vocabulary, not the film. The motion brief's concept and central visual rule decide
  which effect a beat uses and how its result becomes the next scene's bridge.

## MKTC: talking character (talking-character.js, 2026-10-29)

`MKTC.rig(tl, parent, voiceStart, {x,y,w,track,parts,base,seed})` builds a layered character driven by
`talk.json` (mouth cues, loudness envelope, accents); `MKTC.show / look / reaction` add entrances,
glances and beats. Seeded blinks, explicit segments instead of yoyo, every tween a `fromTo` with
`immediateRender:false`. Method and layouts: `references/talking-head-reels.md`.
Unit checks: `node assets/motion-kit/talking-character.test.cjs`.

## MKS: shot & effect library (motion-shots.js, 2026-10-23)

`MKS.orbit, casualCam, uiWorld, frameBreak, digitalZoom, phoneMockup, checklist, headlineWall,
zoomThrough, chartGrid, pullbackReveal, greenScreen, paperGround/paperCut, doodleBoil, vertigo,
coverStory, glassType, slideUpText` and the log-space camera `MKS.logCam`. Same contract as MKFX
(seek-safe, caller supplies words and media, returns handles). Catalogue, story jobs and timings:
`motion-effects-library.md`. Test stage: `projects/mks-gallery` (18 × 3 s, snapshot-verified);
unit checks: `node assets/motion-kit/motion-shots.test.cjs`.


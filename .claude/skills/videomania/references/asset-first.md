# Asset-first: generate real pictures, then let code stitch them

The user's rule (2026-11-14, after the director film v3): "Claude Code keeps trying to build everything on its
own. Every time, FIRST rely on asset generation (ChatGPT / codex), so you get real-looking assets, THEN do your
things on them. Inside the pixel world use the real assets: when we zoom into the computer screen, real editing
clips should play there." This holds for every model. Opus can draw a lot in code; Sonnet cannot draw as well;
both get a better film from the same order of work: **assets first, code second.**

Why it works: a pixel/voxel world made only by code reads synthetic. Real pictures inside it (a glossy icon,
a real app screen, real footage on a monitor) give contrast and credibility — the code world becomes the stage,
the assets become the things on it.

## The asset pass (crew job 4, before any shots.js is written)

1. List every element the viewer will read as an **object, screen, icon, product, place or character**
   (not type, not particles, not transitions). Write `storyboard/assets.json`:
   `[{ "id": "crew-icons", "used_in": ["N"], "source": "gen", "prompt": "...", "file": "assets/gen/icons/sheet.png" }, ...]`
   `source` is one of: `gen` (ChatGPT image bridge), `footage` (real frames: this film, earlier versions, the user's
   clips), `photo` (the user's own pictures), `code` (only with a written reason).
2. Generate in parallel, in the background (3 at a time, 4–6 min each), while you write the shot list:
   - `~/.claude/skills/gpt-image-bridge/bin/gpt-image-2 "<prompt>" <out.png> --size 1536x1024`
   - with a reference (likeness, style, same character): `scripts/gpt_image_ref.sh "<prompt>" <out.png> --ref <img>`
3. Cut sheets of objects with `scripts/pose_sheet.py` (it works for any grid of things on magenta, not only poses).
4. Look at every picture before using it. Regenerate what is off.

## What to generate for what (table)

| element in the film | asset | how |
|---|---|---|
| icons on cards (roles, tools, steps, ideas) | one **icon sheet**, 5×2 glossy 2.5D tiles, "NO pink or magenta in the icons", magenta background | gpt-image-2 → `pose_sheet.py sheet.png --names a,b,... --tall 256` → `cards: [{ img }]` |
| a monitor / phone / laptop screen | a **real app screenshot** (editor with timeline, code editor with the actual file, chat, analytics) | gpt-image-2, 16:9 → `screen: { kind: "image", src, zoom, at }` |
| "this video", "watch", "the result", a clip | **real footage**: frames of this very film (render a draft first), earlier versions, the user's clips | `ffmpeg -ss A -t D -i film.mp4 -vf fps=10,scale=680:370 f_%03d.jpg` → `screen: { kind: "frames", src: ".../f_%03d.jpg", count, title }` |
| versions, history, a gallery | **real frames** from earlier renders / the user's work | `fan: { imgs: [...] }`, `strip: { imgs: [...] }` |
| a world / backdrop / place | a **photoreal or painted plate** + depth map | gpt-image-2 → `vm_depth.py` → relief set (`sets/meadow.json`, `vista.json`) or `SHOTS.plates` |
| the host / a character | the **creator's mascot from their photo**, pose sheets | `references/mascot-from-photo.md` |
| a held object (the file, a product) | part of the mascot pose (hold_doc) or a generated object picture | pose sheet / gpt-image-2 |

Prompt patterns that work: name the style ("premium glossy 2.5D app icon", "realistic dark-theme app UI,
generic, no brand names"), the layout ("strict grid 5×2, wide empty space"), the background ("solid flat pure
magenta #FF00FF") and what to avoid ("no text labels", "no pink or magenta in the art").

## What code still does (the stitching)

Camera paths, light, depth, the pixel world itself, kinetic type, the mascot's acting, particles, washes,
transitions, sound. (The doodle marker layer exists in the kit but is OFF for this user since v5.) Code moves and lights the
assets; it does not replace them.

## The gate

`brain.py check` fails a shot list that draws in code what should be an asset: screens of kind
player/code/timeline/chat without a `src`, cards without `img`, fans/strips without `imgs`, `doc` props.
Keep a drawn element on purpose only with `drawn_ok: "<reason>"` on the shot (the director film keeps its
"slop" strip drawn: generic sameness is the point).

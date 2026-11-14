# A mascot from the creator's photo — smooth, recognisable, acting every line

Built for the director film v3 (2026-11-14). The user's notes: "his mascot looks authentic, yours does not";
"make it look like me"; "more clear, smaller pixels, smooth"; "when the voice says Souvik made that thing,
my mascot should be sitting on a chair writing code"; "the Claude mascot jumps over things, sometimes sits
down and codes". Follow these steps exactly; every model (Fable, Opus, Sonnet) gets the same result.

## 1. Hero design (one call, 4–6 min, run in the background)

Only with a photo the person gave you for this purpose.

```bash
S=<skill>/scripts
$S/gpt_image_ref.sh "Design a mascot character of the man in the attached photo, for an animated explainer film. MUST clearly look like him: <hair>, <glasses>, <skin>, <facial hair>, <expression>. Outfit: <clothes from the photo>. Style: premium modern pixel art like a high-end indie game hero sprite: SMALL fine pixels (character about 140 pixels tall, scaled up cleanly), smooth shading with 3-4 tones per colour, <rim light colour from the photo> rim light on one side, clean dark outline, appealing slightly stylised proportions (head about one third of body height, friendly, not a tiny chibi). Full body, standing relaxed, 3/4 view facing right, arms loose. Background: solid flat pure magenta #FF00FF, perfectly uniform, no floor shadow, no text, figure fully inside the frame with generous margin." \
  <project>/source/assets/mascot/hero.png --ref <photo> --size 1024x1536
```

Describe the face in words too (hair, glasses shape, beard): the words keep the likeness when the
reference is weak. Look at the result; if it does not look like the person, regenerate before going on.

## 2. Two pose sheets (two calls in parallel), the hero as reference

The shared start of the prompt (keeps it the same person):

> Character sheet of THE SAME mascot as the first attached image (exact same face, …, same outfit), likeness
> from the second attached photo. Same premium fine pixel-art style as the first image. Layout: a strict grid
> of 4 columns x 2 rows, ONE full-body pose per cell, every pose the same size (character about 85% of the
> cell height), each pose fully separated by wide empty space. Background: one solid flat pure magenta
> #FF00FF everywhere, no floor, no shadows, no text, no labels, no grid lines. Poses, left to right, top row
> then bottom row: …

Sheet A: talk (open hand), point (whole arm), walk (side, mid-stride), jump (feet off ground, arms up),
sit_code (office chair + small desk + laptop, typing), think (hand on chin), cheer (fists up), wave.
Sheet B: run, floor_code (cross-legged, laptop on lap), shrug (palms up), fly (superhero, horizontal),
hold_doc (holding a glowing paper document), surprised (hands on cheeks), holo_type (typing on a floating
holographic keyboard), thumbs (thumbs up, wink).

`--ref hero.png --ref <photo> --size 1536x1024`, output `sheet_a.png`, `sheet_b.png`.

## 3. Cut, key and scale

```bash
python $S/pose_sheet.py sheet_a.png --names talk,point,walk,jump,sit_code,think,cheer,wave \
    sheet_b.png --names run,floor_code,shrug,fly,hold_doc,surprised,holo_type,thumbs -o me --tall 260 --ref-pose talk
python $S/pose_sheet.py hero.png --names idle -o idle_tmp --tall 262   # then copy idle.png into me/ and add it to poses.json
```

`--tall 260` = 260 sprite pixels for a standing pose: at 1080p each sprite pixel is about 2 screen
pixels — fine and smooth (the user rejected big pixels twice). Always open `me/preview.png` and check
every name matches its picture; the order is rows top to bottom, then left to right.

## 4. In the film

```js
cast: { me: { poses: "assets/mascot/me/poses.json", tall: 12.5, head: 0.8, ref: "talk" } }
```

- `tall` 12–13 matches the built-in cast and the studio furniture.
- Missing poses fall back (`happy`→cheer/thumbs, `sit`/`code`→sit_code, `fly`→jump…), so old shot lists work.
- The kit breathes the picture (1.2 % scale), bounces it on syllables while talking, steps it when walking.
- **Every pose change goes through a pixel dissolve** (`dissolve: [t]` 0.05–0.1 s before the act's start):
  the character re-forms instead of popping.

## 5. Acting: the pose says what the line says

| the line is about… | pose |
|---|---|
| a question everyone asks / a myth | shrug |
| asking, wondering, "the difference?" | think |
| naming, "this video", "the top" | point (at the thing) |
| making, writing, building, fixing, "did it himself", "six versions" | **sit_code** (at a desk) or floor_code |
| typing a prompt, teaching Claude, assembling the crew | holo_type |
| the file, the skill, the framework | hold_doc |
| a win, "better", "level", "crew" | cheer, jump |
| "you can too", "the hard part is done", "comment" | thumbs |
| greeting, refusing ("no, not a course") | wave |
| "let's get into it", travel | fly / run / walk |
| shock, the reveal | surprised |

Give each long take 2–4 acts on the words. The Claude robot (`bit`) gets its own acts: jump over cards,
fly, run in — two characters doing different things is what makes a frame feel alive.

## 6. Framing

The mascot is wider than the old code sprites in some poses (sit_code, fly, run). Frame on a third with
the camera 28–36 units away; never crop the head; words go on the other side. Close-ups (fov 26–30)
only for one beat (e.g. coding at the desk), then back out.

## 7. 2.5D: depth, light and shadow on the mascot (v4)

After cutting the poses, make a depth map per pose:

```bash
python <skill>/scripts/pose_depth.py assets/mascot/me/poses.json
```

The kit then turns each sprite into a relief (the mesh is pushed toward the camera by the depth, `lift` 0.9 by
default in `SHOTS.cast.me`) and lights it from the set's key light with normals from the depth: a lit side, a
shadow side, darker recesses (ambient occlusion), a soft sheen, the rim light. The face and shape stay exactly
as generated; the mascot reads as a 3D toy instead of a sticker. `flat: true` on a cast entry turns it off.

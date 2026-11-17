# Director-film runbook: from a voiceover to the finished film, step by step

The exact order of work that produced the user's approved **director film** (v5, 16:9, and the v6 reel,
2026-11-14). It is written so that **any model (Sonnet 5.5, Opus, Fable) gets the same film by following it
literally.** Do the steps in order, run the commands as written, and do not skip a "done when". Where a step
says "read", read that file before acting: the reasoning lives there, the order lives here.

Use this route when the user gives a **voiceover** (or a script) for a narrated explainer, a story about
themselves or their work, or says "like the director film" / "voxel" / "pixel world". Other routes
(talking-head reels, Vox posters, raw clip edits) are in `SKILL.md` → "Pick the route".

Worked example to copy at every step: `templates/voxel-diorama/examples/director-film-v5.shots.js`,
`director-film-v5.score.sh`, `director-film-v5-reel4x5.shots.js`.

> **Faster:** every step below has a `vm` command (`references/claude-editor.md`): `vm new`, `vm hear`, `vm plan`,
> `vm shots --from-recipe`, `vm check`, `vm look`, `vm score`, `vm render --reel`, `vm fx`, `vm deliver`, `vm brain log`.
> This page stays the reference for what each step means and how to judge it.

## Names used below

```bash
S=<the folder that holds this skill>/scripts                       # resolve it; never assume a host path
PY="$HOME/video-production-workbench/OpenMontage/.venv/Scripts/python.exe"   # Linux/mac: .venv/bin/python
P="$HOME/video-production-workbench/OpenMontage/projects/<film-id>" # kebab-case id
HF="npx hyperframes@0.8.166"                                       # pin the version that rendered the film
GEN="$HOME/.claude/skills/gpt-image-bridge/bin/gpt-image-2"         # ChatGPT image bridge (codex)
```

Hard limits on this machine: **one render or snapshot at a time** (each takes ~7 GB of RAM); image
generations take 4–6 min each, run 3 at a time in the background; never claim to have heard audio (sound is
measured). Write Python patches to a file and run it; bash heredocs break on apostrophes.

---

## Step 0. Rules before anything (2 min)

1. Read `references/house-rules.md` (the user's own notes; they override every default).
2. Ask the format if the user did not say it: **16:9**, **reel** (4:5 film in a 9:16 frame, black bars) or
   **full 9:16**. The reel is this user's "short / reels format"; see Step 11.
3. `"$PY" "$S/preflight.py" --input "<voiceover>"`.
4. **Launch OpsGen first** (`bash <repo>/opsgen/opsgen-dev.sh desktop`) and, once the film exists, `vm studio <film>`:
   the person watches every stage land (`references/opsgen.md`).

**Done when:** format known, preflight green.

## Step 1. Hear it: word times (5 min)

```bash
"$PY" "$S/ingest.py" --project <film-id> --audio "<voiceover.mp3>"
```

Writes `transcript/` with every word and its time. Fix misheard words only through
`transcript/corrections.json`. Every time in the shot list comes from these word times.

**Starting from a script only (no recording)?** Voice it locally first (Kokoro, no account, about 20 s):
`npx hyperframes@0.8.166 tts <script.txt> -o <project>/input/vo.wav`, then ingest the wav with
`--language en`. Check the length it reports: that is the film length. (Used for clip10, 10.15 s.)

**Done when:** you can read the whole script with times, and names (the creator's name, product names) are right.

## Step 2. Plan with the brain (10 min)

```bash
"$PY" "$S/brain.py" recall --brief "<one line about the film>"
"$PY" "$S/brain.py" ideas  --brief "<one line>" --project "$P"     # write the result to brief/ideas.md
```

Pick one concept (a single device the whole film plays, e.g. "a heist on the magic-prompt myth"), a hook, a
signature move, and one constraint. These go into `SHOTS.meta` later.

Then cut the voiceover into **chapters**, one per idea (2.5–20 s each), never a clock. Read
`references/rhythm-and-direction.md` §1–3. For each chapter write: time span, idea, the world (set), what the
host does, which words are big. Plan the opening per §2/§2b: a **real world** (photoreal plate) that switches
into the **pixel world** through a screen.

**Done when:** `brief/ideas.md` and a chapter list exist, every chapter has a reason ("why this, why now").

## Step 3. The asset pass — FIRST, before any shot is written (30–60 min, in the background)

Read `references/asset-first.md`. The user's rule: generate the real things first, then let code stitch them.

0. `new_film.py` (Step 5) makes the folders; run it first, then generate into `source/assets/`.
**REUSE BEFORE GENERATING.** The creator's mascot (`source/assets/mascot/me/`), the glossy icon sheet
(`assets/gen/icons/`: prompt, script, storyboard, animation, captions, skill, sound, mix, voiceover, course),
the app screens (`assets/gen/editor_ui.png`, `code_skill.png`, `viral_feed.png`), the orange stage backdrop and
the photoreal meadow plate are bundled in the skill (`assets/voxel-starter/`, see its README). `new_film.py` (Step 5) copies them in by default. Generate only what the new film needs that is not there. A 10 s clip
usually needs no new generation at all; new *derived* pictures come from `scripts/split_frames.py`
(the two-worlds split monitor) or ffmpeg/PIL.

1. Write `storyboard/assets.json`: every object, screen, icon, place and character the viewer will see.
2. Start the generations (3 at a time, `run_in_background`):

| need | command |
|---|---|
| icons for cards (crew roles, tools, steps) | `"$GEN" "<5x2 sheet of glossy 2.5D app icons: ...; strict grid, wide empty space, solid flat pure magenta #FF00FF background, NO pink or magenta in the icons, no text>" "$P/source/assets/gen/icons_sheet.png" --size 1536x1024` then `"$PY" "$S/pose_sheet.py" icons_sheet.png --names a,b,c,... -o "$P/source/assets/gen/icons" --tall 256` |
| an app screen on a monitor | `"$GEN" "<realistic dark-theme video editor UI with timeline, generic, no brand names>" "$P/source/assets/gen/editor_ui.png" --size 1536x1024` |
| a backdrop / world | `"$GEN" "<photoreal meadow at golden hour with a lone computer on a desk ...>" "$P/source/assets/plates/open_world.png" --size 1536x1024` then `"$PY" "$S/vm_depth.py" "$P/source/assets/plates/open_world.png"` (writes `open_world_depth.png`, which `sets/meadow.json` reads) |
| real footage on screens | render a draft first, then `ffmpeg -ss A -t D -i renders/draft.mp4 -vf fps=10,scale=680:370 source/assets/clips/this_video/f_%03d.jpg` |
| earlier versions / a gallery | one frame per earlier render: `ffmpeg -ss T -i v1.mp4 -frames:v 1 source/assets/clips/versions/v1.jpg` |

3. Open and look at every picture. Regenerate anything off (wrong colours, text in the art, magenta inside the art).

**Done when:** every row of `assets.json` has a file you have looked at; nothing the viewer reads as a thing is
left to be drawn in code (unless the shot carries `drawn_ok: "<reason>"`).

## Step 4. The host: the creator's own mascot (1–2 h, in the background, once per creator)

Only with a photo the person gave for this. Follow `references/mascot-from-photo.md` §1–3 and §7 literally:
hero (`gpt_image_ref.sh --ref <photo>`), two pose sheets (`--ref hero.png --ref <photo>`), `pose_sheet.py`
(`--tall 260`, fine pixels), add `idle`, then `"$PY" "$S/pose_depth.py" source/assets/mascot/me/poses.json`
for the 2.5D relief. Open `me/preview.png`: every name must match its picture. **Re-use** the mascot in later
films of the same creator; don't regenerate it.

**This user's mascot already exists** (17 poses + depth, approved): copy
`~/video-production-workbench/OpenMontage/projects/director-film/source/assets/mascot/me/` into the new
project's `source/assets/mascot/me/` and skip to Step 5. It is their likeness: keep it on this machine, never
in a public repo.

**Done when:** 17 poses + depth maps exist, and the hero looks like the person.

## Step 5. The project page (1 command; do this BEFORE Step 3's generations)

```bash
"$PY" "$S/new_film.py" "$P" --duration <voiceover seconds> [--size 1920x1080] \
      [--assets-from <earlier project> | --no-assets]
```

It copies the kit into `source/`, sets the page size and `#root` duration, adds
`<audio id="mix" src="mix.wav">` (the mix lands there in Step 8), writes a skeleton `source/shots.js` and makes
the asset folders; it also copies the bundled starter assets (`assets/voxel-starter/`: the approved mascot with depth maps, icons, screens, backdrop, plates; `--assets-from` takes them from an earlier project instead).
**Never put a second HTML file with a `data-composition-id` inside `source/`** (`hyperframes check` fails with
`multiple_root_compositions`): `reel_frame.py` keeps its backups in `<project>/_landscape/` for that reason.
Windows note: Python cannot open `/c/...` paths; pass relative paths or `C:/...` to Python, and `cd` into the project.

## Step 6. Write `source/shots.js` (1–2 h)

Start from `examples/director-film-v5.shots.js` and replace the content, keeping its shape. Field reference:
`templates/voxel-diorama/README.md`. The rules, each tested on the user:

- **One shot per chapter**, `t0`/`t1` on word times, no gaps. The camera moves through the take
  (`cam.keys`, 2–4 keys); inside it something changes on the words every 2–3 s (camera key, `wash`, a
  pose change with `dissolve`, a new word group). Cuts (`out`) only at chapter turns.
- **Words around the subject, never on it:** `type: { compose: true, depth: true }`, each word placed with
  `C(x, y, { size, rot, tilt, arc, from })`; the host on one third, words on the other. Punch words big.
- **The host acts the line** (pose table in `mascot-from-photo.md` §5): "he built it" → `sit_code`, "the
  file" → `hold_doc`, "a myth" → `shrug`. 2–4 acts per long take, a `dissolve` 0.05–0.1 s before each.
  A second character (`bit`) does physical things (jump, fly, run in).
- **Real assets on everything** (Step 3): card `img`, `screen: { kind: "frames" | "image" }`, `fan.imgs`,
  `SHOTS.plates`. No doodles (the user removed them).
- Every shot has a `why`. `SHOTS.meta` holds film id, concept, device, hook, signature, structure, constraint.
- Sharp picture: `lens: { aperture: 0.35 }` or lower; blur only when motivated. Crisp grade (`lens.sat`, `contrast`).

- **Plan the "impossible moment" now** (the gate demands at least one): a word flying through the lens
  (`type3d: [{ text: "SECRET.", t, at: [-9, 13, -40], size: 5.5, anim: "through", role: "punch" }]`, keep it off the
  host: put the host `stage-right` and the word left and high), a host or robot flight, vertigo, or a world made
  from a picture. Also three kinds of cast action (`pose`, `jump`, `fly`) or the gate warns.
- **A short clip (about 10 s) = 4 shots**: question, the statement in the void set, the answer (the idea shown on a
  monitor the camera falls into), the sign-off on the generated stage. See `examples/clip10-short.shots.js`.
- **Two worlds on one monitor** (the split-screen device): `scripts/split_frames.py` builds the frames from two
  existing assets; the shot uses `screen: { kind: "frames", src: ".../f_%03d.jpg", count: 40 }` and the camera falls
  into the screen so the merge ends the shot; the next shot (`out: "pixelate"`) lands in the generated world.
- A drawn screen is allowed only with `drawn_ok: "<why>"` on the shot (the drawn world that the film argues against).
- The skeleton `shots.js` is already in place: read it, then overwrite it (the Write/Edit tools refuse unread files).

```bash
"$PY" "$S/brain.py" check "$P/source/shots.js" --project "$P"     # must print PASS (rhythm, novelty, asset-first, why)
"$PY" "$S/brain.py" beats "$P/source/shots.js"                    # second-by-second map; no dead seconds
```

**Done when:** `brain.py check` passes.

## Step 7. Look before rendering (20 min per pass)

```bash
cd "$P/source" && $HF check
$HF snapshot --at 1.2,4.2,<one time per chapter> --no-end --describe false -o ../snaps_a
```

Open the contact sheet and the frames. Fix: a word on a face or off the frame, overlapping words, a head
cut off, a card outside the frame, a pose that doesn't match the line, a blurry background. Repeat until clean.

**What `hyperframes check` says that is not a defect** (judge on frames, do not hack around it):
- `http_error: 404 loading assets/clips/<x>/f_d.jpg`: the frame preloader probing the `%03d` pattern; the frames
  themselves play (look at the snapshot). Seen on every film that uses `screen.kind: "frames"`.
- A contrast failure at exactly a word group's start time (for example t=7.338 for a group at 7.34): the sample
  hits the letters in their entrance animation. Look at a frame 0.3 s later; if it reads, move on.
- A contrast failure well after the entrance IS real: white or coloured words over a bright area (a red rug, a
  lit lamp shade, a bright screen panel). Move the words onto a dark area (the night window, top right) in `type`.

**Defects the snapshots caught in clip10 (look for them every time):**
- the host's head hiding a 3D word, or a word brushing the face: move the host to the other side;
- a middle camera key that drops the host out of the frame (keys must keep the host and the screen in view);
- icon cards cut by the frame edge or by the screen: pull `at` toward the centre, `scale` 0.9;
- a flying cast member that is off-screen at the sampled time (a path starting out of frame): keep paths in view or
  give the arrival a plain pose with `dissolve`, as v5 does;
- words over the screen content: fine when the screen is dark, flagged when it is bright.

## Step 8. Score by meaning (1 h)

Read `references/audio-cinematography.md` (all of it). Then:

```bash
"$PY" "$S/music_map.py" audio/music/*.mp3 -o "$P/audio/music_map.json" --sheet "$P/audio/music_map.png"
```

Cast one song per idea, enter on a downbeat from the map at a chapter turn, leave 2–4 a cappella moments,
bookend the hook song, make the literal jokes (`--dip`). Write the cues as a script, `audio/score.sh`, copied
from `examples/director-film-v5.score.sh` (one `--cue` per entrance), and run it:

```bash
S="$S" P="$P" VOICE="input/<vo>.mp3" bash "$P/audio/score.sh"
```

It writes `source/mix.wav` and prints p10/p50/p90. **Targets:** within 1.5 dB of −22.1 / −14.4 / −11.7 LUFS;
`--music-db -22` (the user wants the music clearly audible: "a little louder" than −26). Never say you
listened; give the user the timestamps of each entrance, drop and joke to check.

Short clip scoring (clip10): a cappella for the opening question, one driving song entering on a downbeat at the
statement (`glitz_ritz.mp3@0.766`), a bright song on the payoff (`mozart_nachtmusik.mp3@2.392`); the measured
spread landed at -20.9 / -14.5 / -11.0, inside 1.5 dB of the reference. Score: `examples/clip10-short.score.sh`.
**Songs are not in the repo** (commercial tracks, public repository): put your own licensed or royalty-free songs in `<project>/audio/music2/`, run `music_map.py` on them, and take the entrance times from your own map. The cue file names in the examples are the ones the director film used.

## Step 9. Render (15–25 min for ~2 min of film; nothing else running)

```bash
cd "$P/source" && $HF render -o ../renders/<film-id>.mp4
```

Then frames from the render at the hook (0.5, 1.5, 3 s), every chapter turn and the end; `ffmpeg -i ... -af
ebur128 -f null -` → integrated about −14 LUFS, peak ≤ −1 dBFS.

## Step 9b. Editor effects and hook sound (5 min; EVERY film)

Read `references/editor-effects-and-hook-sound.md`. The render is the edit; this pass is what a CapCut / Premiere
editor adds on top: the hook on frame 0, a pattern interrupt at every chapter turn, a hit on punch words, each
effect with its sound.

```bash
"$PY" "$S/fx_pass.py" plan "$P"                                   # -> storyboard/fx_cues.json from the shot list
#   read the plan; swap any effect whose job does not fit the line (fx_pass.py list)
"$PY" "$S/fx_pass.py" check "$P/storyboard/fx_cues.json"          # must print PASS
"$PY" "$S/fx_pass.py" apply "$P/renders/<film>.mp4" "$P/storyboard/fx_cues.json" -o "$P/renders/<film>_fx.mp4"
```

Then frames at 0, 0.1, 0.2, 0.4 s (the hook must be visible on frame 0) and at every cue, and the loudness (-14 LUFS,
peak about -1.5 dBFS). **Reel:** apply the same cues to the 4:5 render, THEN `reel_frame.py pad` (Step 11).
**Done when:** `check` PASS, frame 0 shows the hook effect, the film measures -14 LUFS.

## Step 10. Critic pass (max 3 rounds)

Self-check against `references/rhythm-and-direction.md` "Checklist before rendering" and
`crew/08-critic.md`. Fix the top defects on real frames, re-render. Stop after 3 rounds.

## Step 11. Formats

| user says | do |
|---|---|
| 16:9 / YouTube | the render from Step 9 |
| **reel / short / 9:16 "with the video in the middle"** | compose at 4:5 and pad (below). This user's default for reels. |
| full vertical 9:16, re-composed | `reel_frame.py prep source --size 1080x1920 --keep 0.62`, then render without pad. Only when asked |

```bash
cd "$P"
"$PY" "$S/reel_frame.py" prep source --size 1080x1350 --keep 0.82
cd source && $HF snapshot --at <the busy moments> --no-end --describe false -o ../snaps_reel && cd ..
#   any card or prop now outside the frame: move it toward the centre in source/shots.js (e.g. at: [9, 9.5, 2] -> [5.5, 10.5, 3]); change nothing else
cd source && $HF render -o ../renders/<film-id>_4x5.mp4 && cd ..
"$PY" "$S/fx_pass.py" apply renders/<film-id>_4x5.mp4 storyboard/fx_cues.json -o renders/<film-id>_fx_4x5.mp4   # effects BEFORE the bars
"$PY" "$S/reel_frame.py" pad renders/<film-id>_fx_4x5.mp4 renders/<film-id>_reel_9x16.mp4
"$PY" "$S/reel_frame.py" restore source
```

Never a 16:9 strip in a 9:16 frame (the user: "still landscape"); never re-design the film for the reel.

## Step 12. Deliver and learn

1. Copy the film(s) and the captions (`$P/transcript/captions.srt`, written by `ingest.py`, renamed to match the film) to `C:\Users\MSI\OneDrive\Desktop\video editor\output\<film-id>\`.
2. Report only verified facts: file, size, length, loudness, the frames you checked, what is not done.
   Songs: commercial tracks are for private viewing only.
3. `"$PY" "$S/brain.py" log "$P/source/shots.js" --film <film-id>`; after the user's verdict add
   `--verdict "<their words>" --good|--bad`, then `brain.py learn`.
4. **Every note from the user becomes a rule** (`SKILL.md` §4b): fix the film, add a row to
   `references/house-rules.md`, a lesson in `brain/lessons.md`, a check in a script where it can be measured,
   then `bash "$S/install_skills.sh"`.

## Short-clip lane (10-15 s), the whole run in order

1. Step 0, then script -> `tts` -> `ingest` (Step 1). 2. `brain.py ideas` and a one-line concept (Step 2).
3. `new_film.py --assets-from director-film` (Step 5); `split_frames.py` if the device is the split monitor.
4. Write `shots.js` with 4 shots from `examples/clip10-short.shots.js`; `brain.py check` PASS (Step 6).
5. Snapshot every chapter, fix the defects listed in Step 7 (two rounds is normal).
6. `audio/score.sh` from `examples/clip10-short.score.sh`; the spread within 1.5 dB (Step 8).
7. Render 16:9 (about 1 min for 10 s); `fx_pass.py plan / check / apply` (Step 9b: the hook on frame 0, hits, sounds);
   frames from the result, loudness (-14 LUFS); then the reel: render 4:5, apply the same cues, pad (Step 11).
8. Deliver to `output/<film-id>/` with the `.srt`, shot list and score.

Measured on clip10 (Sonnet 5.5): about 25 renders-and-snapshots minutes in total; each render of 10 s = 1 min.

## Self-test log (the skill is tested by running a weaker model on it)

| date | model | task | gaps found, now fixed |
|---|---|---|---|
| 2026-11-14 | Sonnet 5.5 | 10 s clip "generate the assets first" (`examples/clip10-short.*`) | backup `index_landscape.html` inside `source/` broke `hyperframes check` -> `reel_frame.py` backs up to `_landscape/`; kit page had no audio tag -> `new_film.py`; no script-only start -> TTS line in Step 1; no asset reuse step -> Step 3 and `--assets-from`; the brain's "impossible moment" gate was a surprise -> planned in Step 6; Windows Python `/c/` paths; `check` false alarms documented in Step 7 |

| 2026-11-15 | Opus 5.5 | effects pass on clip10 | the kit faded in from black (frame 0 dead) -> no fade by default; the hook effect's attack left frame 0 clean -> `slam` envelope; the planner dropped big moments for small ones -> importance ranking; a 4:5 render made before a kit fix stayed black on frame 0 -> re-render the reel after kit changes |

Add a row every time the skill is run by another model. Fix the gap in the skill, never only in the film.

## When the user asks for a change to a delivered film

Change only what they named ("don't redesign the whole thing"). Copy the shot list to a new version
(`shots_v6.js`), make the edit, keep the old render, re-render, and say exactly what changed.

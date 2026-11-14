# Orchestration: many engines, one film

Video Mania is the conductor. The 47 engines in `engines/engines.json` are the players. A film is not
"made with engine X": each **shot** goes to the engine that plays it best, and all of them are held to
one score so the result looks like one hand made it.

## 1. The score (what every engine receives)

Before any engine is called, the Director, Storyboard artist and Art director (crew jobs 2–4) have fixed:

| Part of the score | File | Binds every engine to |
|---|---|---|
| Time | `storyboard/shots.json` | shot start and end from the voiceover's word times; cues on words |
| Look | `brief/motion_brief.md` | palette roles (ground, voice, accent, type), light, grain |
| Type | `brief/motion_brief.md` | the three type roles; captions' one home |
| Sound | `storyboard/sfx_cues.json` | one mix, made once, at the end |
| Continuity | `storyboard/shots.json` (`in`, `out`) | what the eye is on at each cut, and where |

A shot handed to an engine is one **hand-off card** (`storyboard/handoff/<shot-id>.json`):

```json
{
  "shot": "s07", "engine": "lemo-opuscar", "pocket_id": "lemo/watercolor",
  "duration_s": 4.2, "size": [1920, 1080], "fps": 30,
  "what_it_shows": "the coffee farm at dawn; a hand picks one red cherry",
  "words": [["one", 31.2], ["cherry", 31.5]],
  "palette": {"ground": "#f4efe4", "voice": "#c8121f", "accent": "#19c8b9"},
  "in":  {"eye_at": "lower-left third", "on": "a red dot", "motion": "moving right"},
  "out": {"eye_at": "centre", "on": "the red cherry, 20% of frame height", "motion": "push-in"},
  "deliver": {"file": "assets/shots/s07.mp4", "alpha": false, "audio": "none", "first_and_last_still": true},
  "rules": ["no text in the picture: type is added by the conductor", "no camera stop at either end"]
}
```

The engine's own rules apply **inside** the shot. The card's rules win at its edges.

## 2. Who plays what

| The shot needs | Engine (lane) | Comes back as |
|---|---|---|
| A host in a world, UI on a screen, numbers, type-led beats | **voxel-diorama kit** on HyperFrames | page |
| Kinetic type, UI mockups, data, logos, icons | HyperFrames + motion kit, motionmaxxing eases, bang-motion, iart-kinetic-type, varg-skills | page |
| A named film style | lemo-opuscar (68 styles) | page or clip |
| A painting that moves | huashu-art-motion (uv) | clip |
| Drawn stroke by stroke, doodles, whiteboard | claude-drawing-skill, anidoodle, whiteboard-animation-vi | clip |
| A hand-drawn character acting | ClaudeAnimationBase | clip |
| Pixel art: scenes, sprites, the pixel switch | pixel-studio, the kit's cast and `pixelate`, aseprite-ai-artist | page, clip or sprite |
| Paper collage, Vox explainer inserts | Vox poster system, vox-director, gbro | page or clip |
| One unbroken take | onetake (personal films) | page |
| Vector characters, stick figures, Lottie, SVG | HyperFrames Lottie adapter, claudedesignskills, iart-web-animation | page |
| Math, graphs, equations | manim-skill (uv) | clip |
| Real 3D: product turntables, worlds, 3D type | **raea** (`tools/raea/raea/bin/raea.exe`), models from `raea gen mesh` or the photo → GLB step | clip (alpha possible) |
| Real-world moving footage | Google Flow, Omni Flash only, one approval each | clip |
| Stills, icons, sticker sheets | ChatGPT images | image |
| Raw footage: cuts, retakes, reframes, loudness | video-use rules, ai-video-editor-cooked, ffmpeg-skill, `cut_speech.py` | clip |
| Format grammar (podcast, interview, listicle) | hypit playbooks | rules for the editor |
| Transitions, effects, stickers, music, sounds | OpenFilm library (CC0) via the Pocket | assets |
| Learning a look from references | cooked teardown, hypit reference method, `analyze_video.py` | a style card in `references/styles/` |

No Blender. 3D is raea, or Three.js inside a HyperFrames page for simple scenes.

## 3. Mixing rules (what makes it one film)

1. **One master timeline.** The master composition is a HyperFrames project. Pages from HTML engines
   are scenes in it; clips from every other engine are `<video muted>` layers on their word times, each
   bracketed with its first and last still. (OpenFilm becomes the master timeline when its adapters are
   built; the hand-off cards do not change.)
2. **Type belongs to the conductor.** Engines deliver pictures without words unless the words are part
   of the picture (a sign, a UI). Captions and kinetic type are added once, in the master, in the
   film's type roles. Two engines never set type in two different faces.
3. **One palette.** The card carries the palette roles. A style with its own strong palette (a
   watercolour, a pixel palette) keeps it inside the shot, and the master bridges with the voice
   colour: a transition, a frame edge or the type in that colour on both sides of the cut.
4. **Bridges are designed.** Every change of engine is a cut the viewer could feel, so it gets a
   bridge: a match on the eye point, an object that carries over, or a transition made from the next
   shot's material (pixel blocks into a pixel shot, a paper tear into a collage, a brush wipe into a
   painting, a blur whip between two 3D moves). Never a plain fade between two engines.
5. **At most three engines per 30 seconds,** and one of them is the home engine that owns more than
   half the runtime. More than that reads as a showreel, not a film.
6. **One grade at the end.** A light shared grade, grain and vignette over the master ties clips from
   different renderers together. Clips from Flow are used exactly as delivered: grade the layer, never
   alter the file.
7. **One sound pass,** after picture lock, over the whole master (crew job 7).
8. **One render at a time** on this machine. Engines render their shots one after another; the master
   renders last.

## 4. The order of play

1. Producer: menu from the Pocket, picks, plan approved.
2. Director, Storyboard, Art director: the score.
3. For each shot: `pocket.py show <pocket_id>`, read the engine's entry pages, write the hand-off card,
   run the engine in its own folder (`projects/<id>/shots/<shot-id>/`), check the delivered clip against
   the card (duration, size, first and last still, no stray text), then place it.
4. Animator and Editor: build the home-engine scenes and the bridges in the master, captions, draft.
5. Sound, Critic, fixes (three passes at most), delivery, Teacher.

## 5. When an engine cannot do its part

Say so in one line, pick the next engine in the same lane (the Pocket lists neighbours), and note it in
the report. Never leave a placeholder in a delivered film. `python scripts/vm_engines.py doctor` shows what each engine
needs on this machine.

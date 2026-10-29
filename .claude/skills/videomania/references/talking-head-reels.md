# Talking-head reels: an animated character from one image, with motion graphics

Trigger: the user gives an image (a face, a mascot, a character, a product mascot) and wants it to
**talk** over their voiceover or script, in a reel packed with motion graphics. This file is the
whole method. Read it with `motion-design-playbook.md` and `vox-poster-system.md`.

## What exists on GitHub (researched 2026-10-29) and what runs on this machine

| Approach | Repo | Needs | Verdict for this setup |
|---|---|---|---|
| Photo + voice to generated speaking shots, plus motion-graphic scenes | `iart-ai/talking-head-skills` (MIT) | paid `FAL_KEY` (MiniMax H3) and `ELEVENLABS_API_KEY` | Works, but paid and uploads the face and voice. Kept as an **optional route R3** only on request, with the user's own keys |
| Audio-driven photo animation | `OpenTalker/SadTalker`, `KlingAIResearch/LivePortrait`, `bytedance/LatentSync`, `Rudrabha/Wav2Lip`, `OpenTalker/video-retalking` | NVIDIA GPU and several GB of VRAM | **Not usable here** (no NVIDIA GPU, about 7 GB RAM). Fine in a GPU cloud session; not the default |
| Phoneme lip-sync track from audio | `DanielSWolf/rhubarb-lip-sync` (MIT) | a small binary, CPU | Best mouth timing for 2D characters. Optional: `viseme_track.py --rhubarb` imports its JSON. Download only with the user's go-ahead |
| 2D rigged character in the page | built into this skill: `MKTC` + `viseme_track.py` + `character_parts.py` | CPU only | **Default route R1** |

## Three routes (pick one per film, say which)

- **R1 Coded character (default).** The image becomes an animated character: eyes blink, head
  bobs with the voice, mouth shapes follow the audio, glances and reactions are timed to the
  story. Free, local, deterministic, seek-safe, works in any HyperFrames composition and in cloud
  sessions. Style: illustrated, 3D-cartoon, sticker, mascot or stylised portrait. A real photo
  works only when stylised first; a photo with pasted mouth patches looks uncanny.
- **R2 Generated speaking footage (photoreal).** Google Flow image-to-video, Omni Flash only,
  never Veo 3.1; the user picks 16:9 or 9:16 and approves **one click per generation**. The photo
  is the start frame; the prompt carries the exact line. Keep the clip's own audio on those shots
  (never dub over it). Use for 1 to 3 short hook / close lines (2 to 8 s each), and the rest of
  the film is graphics. Lip-sync is the model's; check frames and say what you could not verify.
- **R3 Paid API pipeline (optional).** `iart-ai/talking-head-skills` with the user's fal and
  ElevenLabs keys. Only when asked; it is a paid action and uploads the face and voice.

## Consent and honesty (hard rules)

- Use only the user's own face and voice, a character they made, or someone who has said yes.
  Never a real public figure, never a cloned voice without consent, never to make someone appear
  to say something they did not.
- Realistic generated speakers (R2, R3) are labelled AI-generated in the delivery notes.
- Say plainly when lip-sync is an estimate: the built-in estimator maps loudness and spectral
  balance to mouth shapes, it does not recognise phonemes.

## Workflow (R1)

1. **Ask**: 16:9 or 9:16; the voiceover (or the script, then `make_audio.py`); the image(s);
   which look (stylised character vs mascot vs sticker). Preflight as in SKILL step 0.
2. **Design the character** in ChatGPT (see `chatgpt-asset-production.md`, one thread). Upload the
   user's image and ask for the stylised character on a flat or transparent background, front-facing
   three-quarter view, shoulders visible, rest pose: eyes open, mouth closed. Approve the design with
   the user once. Then, **in the same thread, edit the approved image one thing at a time**, each
   with "keep everything identical, only change the mouth / eyes":
   - `mouth_C` (open, EH), `mouth_D` (wide, AH), `mouth_E` (round, OH). Optional: `mouth_B`
     (teeth, slight), `mouth_F` (pucker, OO), `mouth_G` (teeth on lip, F/V), `mouth_A` (lips pressed).
   - `eyes_closed`.
   Slice with `chatgpt_slice.py` if returned as a sheet. All poses must have the same size and framing.
3. **Cut the parts**: `python scripts/character_parts.py --dir poses --out projects/<id>/source/media/char`.
   It diffs each pose against the rest pose, cuts feathered mouth and lid patches, fills missing
   letters from the nearest shape, and prints an alignment verdict. `DRIFT` means the poses moved:
   regenerate those poses, do not ship.
4. **Mouth track**: `python scripts/viseme_track.py --audio <voiceover> --words <transcript.json> --out projects/<id>/source/talk.json`
   (add `--rhubarb out.json` instead of the estimate when Rhubarb is available).
5. **Scaffold**: `new_composition.py ...`. It copies `mk/talking-character.js` and loads it.
6. **Storyboard the cadence** (below), then build scenes with `MKTC` for the character and `MKS` /
   `MKFX` for the graphics. `templates/talking-head/reel.scenes.example.js` is a worked layout set.
7. **Check**: `template_lint.py`, snapshots at accents and blinks, `qa.py`, then the independent critic.

## Reel grammar (character + motion graphics)

The character is never alone on screen for long, and the graphics are never separate from what
the character says.

- **Cadence**: character on screen 40 to 60% of the runtime; no more than 4 s of the same
  composition; every 2 to 4 s a graphic event (a keyword slam, a number count, an object arrival,
  a cut-in) anchored to a spoken word using measured word times.
- **Layouts (rotate through at least three)**:
  1. *Breakout*: character cut-out breaking out of a colour frame, kinetic line in the top zone (Vox).
  2. *Corner presenter*: character in a rounded corner window while the full frame plays the
     explaining graphic (chart, UI, map); glance toward the graphic with `MKTC.look`.
  3. *Behind-type*: giant word behind the character (`MKS.headlineWall` / `slideUpText`), the
     character in front; the word is the hook.
  4. *Split stage*: character on one half, an object or recording (in `phoneMockup`) on the other.
  5. *Cut-away*: the character leaves (`MKTC.show` out) for a full-frame graphic beat, returns on
     the next point with a different layout. Voice continues; mouth hidden is fine.
  6. *Reaction pop*: small character cut-in with `MKTC.reaction(... "surprise")` on a punchline.
- **Face-safe zone**: no graphic over the mouth or eyes. Captions stay bottom-centre on one
  baseline (house rule); keep the mouth clear of the caption band.
- **Gaze**: glance toward the incoming graphic about 0.15 s before it lands, hold 0.8 to 1.2 s,
  return. Reaction only on a real beat (a surprise, a joke, a number), at most 3 per 30 s.
- **Voice-first timing**: graphics lead their anchor word by about 6 frames; withheld answers land
  on their word. Measured word times, never estimates.
- **Sound**: character scenes carry the voice; sparse designed SFX on graphic events (see
  `research-digest-2026-10.md` §5). Music ducked under speech.
- **Opening**: frame 0 already has the character alive (eyes open, mouth shape from the first
  cue) and a specific reason to stay in 3 s; no fade-in from empty.

## Checks specific to talking characters

- Mouth moves only while speech is present: verify `talk.json` cues against the voice (the speaking
  share should match the audio; silence = X).
- Blink schedule exists and is not synchronous with cuts.
- No part shimmer: `character_parts.py` alignment OK; look at a snapshot at a blink and at the
  widest mouth.
- Seek-safe: `template_lint.py` shows no `Math.random`, no `repeat:-1`; MKTC uses seeded blinks
  and explicit up/down segments.
- Do not claim to have heard the sync. Report the measured facts (cue count, speaking share,
  accents) and which frames were inspected.

## Files

| File | Job |
|---|---|
| `scripts/viseme_track.py` | audio (and optional word times or Rhubarb JSON) to `talk.json`: mouth cues, loudness envelope, accents |
| `scripts/character_parts.py` | aligned pose images to feathered mouth and lid patches and `parts.json`, with an alignment gauge |
| `assets/motion-kit/talking-character.js` | `MKTC.rig / show / look / reaction` plus seeded blinks and a vector fallback character |
| `assets/motion-kit/talking-character.test.cjs` | 397 structural checks (determinism, seek-safety, API) |
| `templates/talking-head/reel.scenes.example.js` | worked layouts: breakout, corner presenter, behind-type, cut-away |

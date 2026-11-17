# Editor effects and hook sound: the first second, and every turn after it

**Read this before the render of ANY film** (voxel kit, HyperFrames scaffold, talking head, raw clips). It is the
layer CapCut / Premiere / After Effects editors add on top of an edit: built-in effects (glitch, distortion, shake,
zoom punch, flashes, light leaks, VHS ...) and the hit sounds that come with them.

## Why (the user's numbers, 2026-11-15)

The director film's reel got **200 views, 10 likes and a 65 % skip rate**. The reference reel it was modelled on has
**50K likes**. Side by side, the difference was in the first second: the reference opens on a **"universe
distorted" glitch with an ominous sound**, and keeps re-hooking with editor effects and hit sounds. Our film opened
on a clean frame that faded in from black, with music only. A viewer decides in about 1 s; the first frame and the
first sound are the most valuable moments of the film.

## The tools

```bash
S=<skill>/scripts
python $S/fx_pass.py list                                  # the 41 presets with their story job and paired sound
python $S/fx_pass.py plan <project>                        # an editor's plan from the shot list -> storyboard/fx_cues.json
#   read it, change what does not serve the meaning (it is a plan, not a verdict), then:
python $S/fx_pass.py check <project>/storyboard/fx_cues.json   # gates: hook in 0.3 s, sound on it, flash spacing, density
python $S/fx_pass.py apply renders/<film>.mp4 storyboard/fx_cues.json -o renders/<film>_fx.mp4
python $S/fx_pass.py gallery renders/<film>.mp4 --at <s> -o qa/fx          # every preset on one of YOUR frames
python $S/sfx_library.py find "ominous hit"                # search the 59 hook sounds (id, length, sync point)
```

Order in the pipeline: **render -> fx_pass apply -> (reel: apply on the 4:5 render, THEN `reel_frame.py pad`) ->
deliver.** Effects go on before the black bars so a warp never bends the bars. `apply` mixes every paired sound into
the film's own audio at its sync point, level-matched from measured loudness, and finishes at -14 LUFS, true peak
-1.5 dBTP. It takes about 25 s for 10 s of 1080p.

## 1. The first second (non-negotiable)

1. **Frame 0 is a full, bright picture, already moving.** Never a fade from black (the voxel kit no longer fades in;
   `SHOTS.fadeIn: true` only if the user asks). The hook effect is at FULL strength on frame 0 (envelope `slam`).
2. **One hook effect, 0.5-0.8 s, on frame 0**, chosen by subject:
   - `universe_warp` (default): the world twists, bulges, splits colour and snaps into the film. Any "you won't
     believe" / reveal / "everyone is wrong" opening.
   - `glitch_hook`: tech, AI, hacking, "broken", "error".
   - `shockwave`: a name, a statement, a launch: a ring of force from the subject.
   - `flash_zoom_hook`: bright, energetic, positive subjects.
3. **The ominous hook sound stack on the same frame**, three layers that each own a band:
   transient (`tear`, `digital-corrupt`, `cinematic-slam-big`) + body (`braam`, `cinematic-drum-big`) + sub
   (`bass-sub-drop-short`, `sub_hit`). The preset carries the stack; keep all three.
4. The first spoken word starts within 0.3 s, and words are on screen by 0.5 s.
5. `universe_warp` is used ONCE per film: it is the hook, not an effect.

## 2. Keep re-hooking: a pattern interrupt every 3-7 s

Attention decays; every chapter turn re-buys it. The planner does this from the shot list:

| moment | what goes there | sound |
|---|---|---|
| a chapter turn with a hard cut | a transition: `glitch_cut`, `zoom_cut`, `whip_cut`, `flash_cut`, `pixel_cut` (rotate; never the same twice in a row) | whoosh / glitch peaking ON the cut |
| a kit transition (pixelate, iris, flash, mosaic) | the kit draws it: add only a light `rgb_split` and its SOUND | whoosh or drum on the cut |
| a punch word | one hit: `zoom_punch`, `shake`, `rgb_split`, `chromatic`, `lens_bulge` (rotate) | sub hit / slam on the word |
| a 3D word landing, a name, a launch | `shockwave` | boom drop + sub |
| a build to a reveal | `riser-1s/2s-strong` or `ominous_swell` ENDING on the cut (sync = end), then the hit | silence 0.2 s before the drop makes it bigger |
| the ending | `light_leak` or `film_burn`, or `color_pop` on the last punch | shimmer / sting |

Meaning first: pick the effect whose job matches the line (`fx_pass.py list` gives each job): "wrong / myth / error"
-> `glitch_slices`; "years ago" -> `old_film` / `vhs`; "stop" -> `bw_hit`, then `color_pop` on the answer;
"YOU" -> `lens_bulge`; "fast / instantly" -> `zoom_blur`; "wait..." -> `frame_stutter` / `freeze_hold`.

## 3. Taste: what a 30-year editor never does

- Never an effect without a reason in the story, never on every word: **at most one effect per 2 s on average**, and
  at most one per chapter on punch words. The planner keeps the important ones (hook > chapter turns > 3D words >
  ending > punch words) and drops anything within 1 s of a kept cue.
- Never the same effect twice in a row; rotate families.
- **Photosensitivity:** flash-type effects (flashes, invert, negative) at least 1 s apart, never more than 3 flashes
  in any second (the `check` gate fails it).
- Strongest effect at 0 s; the rest medium (amount 0.5-0.9). Big effects over a face only for a beat.
- Texture looks (`vhs`, `old_film`, `crt`, `film_grain`) are for a passage that means "the past" or "inside a
  screen", never the whole film.
- Every visual effect has a sound, and every hit sound has a picture event. A sound with nothing on screen is noise.

## 4. Sound engineering for hooks

- Every sound in `assets/sfx-hook/manifest.json` has a `sync_at` (the instant that must land on the picture: a hit's
  peak, a riser's END) and a measured `lufs`; `apply` places and level-matches it: hard tier 2 dB under the film's
  loudness, medium 4 dB, soft 7 dB, plus the cue's `gain_db`.
- Layer by band: a transient for the attack, a body for weight, a sub you feel. Glitch textures sit in the highs and
  do not mask the voice; braams and subs sit under it.
- Risers and reverse whooshes END on the cut; whooshes PEAK on the move; hits START on the frame.
- After the pass the film is re-finished to -14 LUFS / -1.5 dBTP; the momentary spread should still match the
  reference (`sound_mix.py` numbers) because the hits are short.
- Never claim to have heard it: report the measured numbers and the timestamps of every hook sound for the user to
  check on a phone.

## 5. The catalogue (41 presets)

| family | preset | length | story job | paired sound | avoid |
|---|---|---|---|---|---|
| hook | `universe_warp` | 0.75 s | Frame 0: the world twists, bulges and splits colour, then snaps into the film. The scroll-stopper. | braam, tear, bass-sub-drop-short | more than once per film |
| hook | `shockwave` | 0.60 s | A ring of force from the subject: a reveal, a 'boom' statement, a name. | boom-drop-medium, sub_hit | busy frames |
| hook | `glitch_hook` | 0.60 s | Frame 0 for tech / AI / hacking subjects: the signal breaks, then locks on. | digital-corrupt, cinematic-drum-big, bass-sub-drop-short | calm or warm films |
| hook | `flash_zoom_hook` | 0.50 s | Frame 0: white flash into a hard zoom punch: energetic, bright subjects. | cinematic-slam-big, whoosh-fast-hard | dark ominous openings |
| transition | `glitch_cut` | 0.36 s around the cut | A glitch across the cut: the default energetic cut. | digital-glitch-clear, whoosh-fast-hard | - |
| transition | `whip_cut` | 0.30 s around the cut | Whip pan across the cut. | whoosh-fast-hard | - |
| transition | `zoom_cut` | 0.40 s around the cut | Zoom through into the next shot. | move-zoom-in, boom-hit-soft | - |
| transition | `flash_cut` | 0.24 s around the cut | White flash across the cut: a new world. | cinematic-drum-big | max 3 flashes per second |
| transition | `pixel_cut` | 0.40 s around the cut | Pixelate out and back in: pixel worlds. | digital-glitch-subtle | - |
| glitch | `rgb_split` | 0.35 s | Colour channels tear apart for a beat: a light accent on a word or a turn. | digital-glitch-subtle | faces in close-up for long |
| glitch | `glitch_slices` | 0.40 s | Horizontal bands jump sideways: 'wrong', 'error', 'myth'. | digital-glitch-clear | warm emotional beats |
| glitch | `digital_glitch` | 0.50 s | Full digital break-up: slices, colour split, corrupt blocks. | digital-corrupt | more than 3 per minute |
| glitch | `block_corrupt` | 0.40 s | Macroblocks smear and posterise: data, AI, broken files. | digital-scramble | - |
| glitch | `static_burst` | 0.30 s | TV snow over the picture: a channel change, a cut to a new world. | digital-static | - |
| glitch | `invert_flash` | 0.20 s | Two-frame negative flicker: a shock word. | sub_hit | photosensitive pacing: max 3 per second |
| glitch | `frame_stutter` | 0.45 s | The picture stammers on its last frames: a double-take, a 'wait...'. | shutter_stutter | - |
| glitch | `signal_drop` | 0.50 s | Signal failing: black lines, jumps, colour loss: a lie, a crash, 'it failed'. | digital-signal-drop | - |
| camera | `zoom_punch` | 0.35 s | Snap zoom-in on the punch word, then settle: the classic emphasis. | sub_hit, whoosh-fast-medium | every word: max one per chapter |
| camera | `zoom_blur` | 0.35 s | Radial speed blur: 'fast', 'instantly', travel. | whoosh-fast-hard | - |
| camera | `shake` | 0.45 s | Impact shake: something lands, a big claim, a slam. | cinematic-slam-big | dialogue-heavy holds |
| camera | `whip_blur` | 0.30 s | Sideways whip: moving on, 'next'. | whoosh-fast-hard | - |
| distort | `lens_bulge` | 0.35 s | Fisheye punch toward the viewer: 'YOU', a direct address. | move-zoom-in | - |
| distort | `wave_warp` | 0.70 s | Heat-haze wobble: a dream, a memory, confusion. | whoosh-slow-hard | - |
| distort | `chromatic` | 0.40 s | Radial colour fringing: lens stress on an impact. | impact-deep-hard | - |
| light | `flash_white` | 0.25 s | A white flash: a reveal, a new world, a camera snap. | cinematic-drum-big | max 3 flashes per second |
| light | `flash_color` | 0.25 s | A flash in the brand red: an alarm word. | boom-hit-medium | - |
| light | `light_leak` | 1.20 s | Warm light sweeping across: nostalgia, a win, the ending. | whoosh-slow-hard, shimmer-short-soft | tense moments |
| light | `film_burn` | 0.90 s | Orange film burn eating the frame: a chapter ending, a memory closing. | whoosh-slow-hard | - |
| light | `flare_streak` | 0.80 s | Anamorphic streak from the brights: premium, cinematic, a product hero. | shimmer-short-soft | dark frames (no brights) |
| light | `bloom_pulse` | 0.40 s | The whole frame glows for a beat: 'magic', 'perfect', a win. | sting-bright-short | - |
| color | `bw_hit` | 0.60 s | Drop to black and white: 'stop', a sober truth, the problem. | sub_hit | - |
| color | `color_pop` | 0.60 s | Saturation surge: the answer, colour returning after bw_hit. | shimmer-short-soft | - |
| color | `red_alert` | 0.60 s | Red tint: danger, wrong, warning. | digital-denied | - |
| color | `negative` | 0.30 s | Full negative: an upside-down idea. | tear | - |
| texture | `vhs` | 1.00 s | VHS tape: the past, 'back then', a flashback. | digital-static | the whole film |
| texture | `crt` | 1.00 s | Old monitor scanlines: inside a screen, retro tech. | digital-power-up | - |
| texture | `film_grain` | 1.50 s | Grain texture: a documentary, 'real' footage beat. | - | - |
| texture | `old_film` | 1.50 s | Sepia, scratches, flicker: history, 'years ago'. | - | - |
| time | `echo_trails` | 0.80 s | Motion trails: speed, a blur of work, 'everything at once'. | whoosh-medium-hard | static shots (no effect) |
| time | `freeze_hold` | 0.80 s | Freeze frame with a push: 'this is me', a record-scratch moment. | tape_stop, shutter_stutter | - |
| time | `pixelate` | 0.40 s | Pixel break-up and resolve: entering a game / pixel world. | digital-glitch-clear | - |

## 6. Sources and licences

- **Sounds**: SFX Kit by Wyzowl (CC0-1.0, github.com/wyzowl/sfx-kit), 51 picked, converted to OGG, with their sync and
  loudness data; 8 original hook sounds from `scripts/hook_sounds.py` (CC0). Bundled in `assets/sfx-hook/`. The
  HyperFrames `media-use` skill's Pixabay sounds and the Barty-Bart CC0 kit (`research/Barty-Bart_motion-graphics`)
  are further sources.
- **Effects**: written for Video Mania in `scripts/fx_pass.py` (numpy + OpenCV, seeded per frame). Techniques studied,
  not copied, from: tomastimelock/video-fx (MIT, 150 named effects in 30 engines), pixijs/filters (MIT: glitch,
  RGB split, shockwave, CRT, old film), gl-transitions (100+ GLSL transitions, per-file licences, mostly MIT),
  pmndrs/postprocessing (zlib). Clones live in `<workbench>/research/` for the next upgrade (a WebGL transition
  layer in the voxel kit is the obvious one).

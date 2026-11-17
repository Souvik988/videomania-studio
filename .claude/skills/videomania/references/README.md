# References: the map

Every reference, grouped by the moment it is needed. **Runbooks** say what to do in which order (follow
them literally); **references** say why and how (open one when a step names it). When two files disagree,
`house-rules.md` wins, then the runbook, then the rest.

## Start here (every film)

| file | open it when |
|---|---|
| `opsgen.md` | **the editor**: launch it first, `vm tl` / `vm edit` timeline operations, `vm media` footage edits, the Claude Code chat |
| `claude-editor.md` | **the command layer**: every step as a `vm` command / MCP tool, one preset search, recipes, the director's brain |
| `house-rules.md` | before every edit — the user's notes as rules, newest first |
| `director-film-runbook.md` | **RUNBOOK** for a narrated film from a voiceover (the approved director film, every command) |
| `director-film-runbook.md` -> Short-clip lane | a 10-15 s clip: the whole run in 8 lines; `scripts/new_film.py`, `scripts/split_frames.py` |
| `input-contracts.md` | checking what an input must look like; formats and delivery specs |
| `pocket-menu.md` | the request is generic ("edit this") — show the menu |

## Think and plan

| file | what it gives |
|---|---|
| `editor-doctrine.md` | how the editor thinks: edit map, visual hook, element palette, pacing, layered frames |
| `storytelling-and-retention.md` | why a viewer stays: a reason by 3 s, open loops, one persistent world |
| `creative-director.md` | concepts, the idea stage |
| `rhythm-and-direction.md` | chapters as long takes, the opening, type around the subject, the measured mix |
| `cinematography.md` | every shot a named choice with a reason |
| `storyboard-and-shot-grammar.md` | shot lists and grammar |
| `low-memory-and-brain.md` | 4–6 GB RAM rules; the director's brain (`brain.py`) |
| `brand-and-reference-analysis.md` | a brand or reference video to measure (`analyze_video.py`) |

## Assets (before any shot is written)

| file | what it gives |
|---|---|
| `asset-first.md` | **the rule**: generate icons, screens, plates, objects, characters first; code stitches |
| `chatgpt-asset-production.md` | the ChatGPT image bridge and the browser-pane fallback; slicing sheets |
| `mascot-from-photo.md` | the creator's own mascot: hero, pose sheets, cutting, 2.5D depth, the acting table |
| `flow-asset-production.md`, `media-sourcing-and-google-flow-mcp.md` | generated video (Omni Flash, one approval per click) |
| `greenscreen-compositing.md` | keying the user's own footage onto a set |

## Build (motion, look, type)

| file | what it gives |
|---|---|
| `motion-design-playbook.md` | how premium motion moves; banned list; 16 effect recipes |
| `motion-kit.md` | tested parts (blueprints, rules, `MK`/`MKFX`), choreography audit |
| `motion-effects-library.md` | 18 tested shots (`MKS`) with their story jobs |
| `motion-and-camera.md` | camera moves and transitions |
| `motion-research-sources.md` | where to research motion (the user's list) |
| `typography-and-captions.md` | the 7-font kit, pairings, captions on one fixed baseline |
| `styles/voxel-diorama.md` | the voxel-diorama house style (kit: `templates/voxel-diorama/README.md`) |
| `editorial-collage-and-diorama.md` | Vox collage and paper diorama |
| `vox-poster-system.md` | the user's "Vox style" (colour editorial poster) |
| `orchestration.md` | mixing several engines in one film |
| `3d-worlds-without-blender.md` | 3D worlds from pictures: generated layers (best), relief plates, `world_build.py` (experimental), SHARP splats (needs 16 GB) |
| `blender-3d-route.md` | optional real 3D (Blender not installed; 3D goes through raea) |

## Sound

| file | what it gives |
|---|---|
| `editor-effects-and-hook-sound.md` | **every film**: the hook on frame 0 (effect + ominous sound stack), pattern interrupts, 41 CapCut-style presets (`fx_pass.py`), 59 hook sounds (`sfx_library.py`) |
| `audio-cinematography.md` | songs cast by meaning, downbeat entrances, a cappella, `sound_mix.py --cue` |
| `background-music-and-sound.md` | SFX design, ducking, the master to −14 LUFS |
| `voiceover-alignment.md` | word times from the voiceover (`ingest.py`) |

## Judge and deliver

| file | what it gives |
|---|---|
| `review-gates-and-critique.md` | QA gates, the independent critic, max 3 passes |
| `research-digest-2026-10.md` | anti-slide-deck rules behind `template_lint.py` |
| `rendering-and-delivery.md` | render, mux, final QA, delivery; reels via `scripts/reel_frame.py` (runbook Step 11) |
| `openmontage-routing.md` | OpenMontage stages, checkpoints, approval policy |

## Special routes

| file | route |
|---|---|
| `talking-head-reels.md` | an image that talks, with motion graphics |
| `greenscreen-compositing.md` | a self-shot talking head on a background plate |

## Where the rest lives

- `../crew/` — nine job pages (one at a time, each with its hand-over and check).
- `../brain/lessons.md` — the brain's lessons (L-1 …), each with evidence and confidence.
- `../templates/voxel-diorama/` — the voxel kit; `examples/director-film-v5.*` is the approved worked film,
  `examples/history/` older versions.
- `../scripts/` — every tool; each prints its own usage with `--help`.

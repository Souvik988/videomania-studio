# Claude Editor: the plan

An agent-first video editor for Claude Code. Claude edits through commands; the person watches the film take shape
in a real timeline, nudges anything by hand, and talks to Claude in a chat box beside it. Personal use first.

## 0. What already exists (audit, 2026-11-15)

| piece | what it is | state |
|---|---|---|
| Video Mania skill | doctrine, runbook, crew, house rules, brain gates, 50+ scripts | works (Sonnet-tested) |
| voxel-diorama kit | Three.js films where every frame is a pure function of t | works, HyperFrames render |
| fx_pass + sfx-hook | 41 editor-effect presets, 59 hook sounds, hook gate | works, post-render pass |
| Pocket | 10,625 rows, SQLite FTS5 + e5 ONNX vectors, 60 engines | works |
| brain | ledger.jsonl, lessons.md, constraints, novelty/surprise gates | works, flat files |
| **OpenFilm 0.3.2** (MIT) | film.html timeline of pages/clips; Studio (browser NLE, edits saved to files); desktop app with a chat for Claude Code/Codex; library: 5,400 CC0 sfx, music, transitions, effects, grades, 1,587 stickers, text and film templates; provider contract for new media services; `look`, `render`, `canvas` | runs here (doctor clean) |

Machine: Ryzen 5 5600H, 7.4 GB RAM, AMD RX 5500M (WebGL, no CUDA), 26 GB disk free. So: one render at a time,
no torch/CUDA models, 3D via WebGL/ONNX, cloud only with the user's approval.

## 1. Architecture

```
            Claude Code (chat in the editor, or this terminal)
                          │  MCP tools / `vm` CLI
          ┌───────────────┴──────────────────────────────────┐
          │  vm  — the editor's command layer (Python)        │
          │  project state · recipes · presets · gates · brain│
          └──┬─────────────┬───────────────┬─────────────┬───┘
     skill scripts   Pocket / presets   director brain   OpenFilm CLI
   (ingest, kit, fx,  (styles, effects,  (vault + vectors, (film.html, Studio,
    sound, reel)       sounds, recipes)   lessons, films)   look, render, library)
                          │
                 Studio (the interface): timeline + preview + library + chat
```

- **The film is a file both sides edit.** Milestone 2 turns a Video Mania project into an OpenFilm `film.html`:
  chapter pages (the voxel kit as a `window.film` page), voice, each song cue, each hit sound and each editor
  effect as its own clip. The person moves a clip in Studio; Claude reads the change from the file.
- **Everything is a command first** (`vm …`, mirrored as MCP tools). The interface only shows them.
- **Recipes** are whole films saved as reusable presets: shot list + score + fx cues + asset list + parameters.
  "Save as recipe" on any finished film; "use recipe" on a new voiceover; recipes combine.
- **Gates are the editor's taste**: brain check, fx hook gate, hyperframes/OpenFilm look, loudness, contrast:
  `vm check` runs all and the interface shows them as a scorecard.

## 2. Milestone 1 — the command layer (`vm`)

| command | does | wraps |
|---|---|---|
| `vm new <film> --voice f / --script f [--format 16:9/reel] [--recipe id]` | project, input, state file | new_film.py, tts |
| `vm status` | stages done, artifacts, the next step, gate results (JSON with `--json`) | vm_next, state |
| `vm hear` | word times | ingest.py |
| `vm plan` | brain recall + ideas, recipe suggestions | brain.py, pocket |
| `vm research "<topic>"` | reference hunt brief (web, Pinterest via browser), decoded moments | firecrawl / analyze_video |
| `vm assets [list/gen/reuse]` | asset pass: reuse starter, generate the rest with the image bridge | gpt-image-2, gpt_image_ref |
| `vm shots [--from-recipe]` | scaffold shots.js from a recipe, retimed to the new words | recipes |
| `vm check` | every gate | brain, fx check, hyperframes check |
| `vm look [t,…]` | snapshots, contact sheet | hyperframes snapshot |
| `vm score` | music map + sound mix | music_map, sound_mix |
| `vm render [--reel]` | 16:9 and/or the 4:5-in-9:16 reel | hyperframes, reel_frame |
| `vm fx [plan/check/apply]` | editor effects + hook sound | fx_pass |
| `vm deliver` | output folder, srt, report | deliver |
| `vm presets search/show` | ONE search over Pocket + fx + sfx-hook + recipes + OpenFilm library | all catalogues |
| `vm recipe save/list/show/use` | whole-film presets | new |
| `vm brain ask/log/learn` | the director's memory | brain v2 |
| `vm mcp` | the same as MCP tools over stdio, registered in Claude Code | new |

Done when: a new voiceover goes to a delivered reel using only `vm` commands (and Claude's writing of the shot
list), every step's state is in `vm status --json`, and the MCP server is registered and answers in Claude Code.

## 3. Milestone 2 — the interface

1. `vm openfilm export`: a Video Mania project -> `film.html` + pages (kit page with `window.film.frame(t)`),
   audio clips per cue, sfx clips, fx as overlay/transition pages; opens in Studio.
2. `vm openfilm import`: read the person's Studio changes back (clip moves, trims, volumes) into the project.
3. Our presets in Studio's library: fx presets as OpenFilm effects/transitions, the sfx-hook sounds, recipes as
   templates, Video Mania as an OpenFilm skill (`openfilm skill add`).
4. The ChatGPT/Codex image bridge as an OpenFilm media provider (`~/.openfilm/providers/gpt-image-bridge/`), so
   "make an image" in Studio and on the canvas uses it.
5. The chat beside the edit is Claude Code (OpenFilm desktop app, or Studio + this session), with the `vm` MCP tools.

## 4. Research tracks (feed presets, 3D and memory into the editor)

- **Presets**: open-source equivalents of CapCut / Premiere / After Effects effects that can run in a browser or
  ffmpeg: CSS animation libraries, GLSL transitions and effects, Lottie animations, LUTs / colour grades, AE
  expression libraries (as knowledge). Whatever cannot run here is rebuilt from scratch in fx_pass or as pages.
- **3D environments without Blender**: image -> world routes that run on this machine (depth reliefs, 360
  panorama worlds, Gaussian splats via Spark, image-to-scene). Build the best one into the kit.
- **Director memory**: an Obsidian-compatible vault (films, lessons, techniques, the user's notes, all wiki-linked)
  indexed by the Pocket's vector engine, written after every film; `vm brain ask` answers from it.

## 5. Rules carried into every milestone

Asset-first (generate with the image bridge before drawing in code) · the hook on frame 0 + hook sound · chapters
not a clock · measured sound (never "heard") · one render at a time · Flow: Omni Flash only, one approval per click ·
no video, songs or voices in the public repo · every user note becomes a rule.

## 6. Status (2026-11-15)

- **Milestone 1 — done and tested.** `scripts/vm.py` (17 commands), `vm_mcp.py` (22 MCP tools, `.mcp.json`),
  `vm_presets.py` (1,020 presets + the Pocket's 10,625 in one search), `vm_recipes.py` (3 recipes),
  `vm_brain.py` (Obsidian vault, 195 notes, keyword + meaning + link search). Proof: `first-second`, a new 8.5 s reel
  from a script to a delivered 16:9 + reel using only `vm` commands. Doc: `references/claude-editor.md`.
- **Milestone 2 — core done and tested.** `vm openfilm setup/export/open/diff/render`: the film opens in OpenFilm
  Studio as an editable timeline; an effect deleted by hand is gone from the Studio render. The image bridge is an
  OpenFilm provider; Claude Editor is an OpenFilm skill.
- **Research brought in.** Effects: EffectCraft (308 AE-equivalent effects, Apache-2.0; its headless MCP needs the
  user's permission to run the downloaded binary), framefields (75 WebGPU nodes), gl-transitions (238), Film-Luts
  (296 grades, `vm grade`). 3D: SHARP installed but out of memory here; `world_build.py` experimental; generated
  layers are the route (references/3d-worlds-without-blender.md). Memory: own vault instead of claude-mem.
- **Next.** EffectCraft as an AE backend (once allowed); our effects as live WebGL pages in Studio (move an effect,
  not just delete it); the voxel kit as an OpenFilm page (`window.film.frame(t)`) so chapters re-render inside Studio;
  recipes as Studio templates.

## 7. Status (2026-11-15, evening): OpsGen

- **OpsGen = our editor.** The whole OpenFilm monorepo (MIT) forked into `opsgen/`, rebranded by script (name, logo,
  CLI `opsgen`, data folder `~/.opsgen`), built outside OneDrive (`opsgen-dev.sh`). OpsGen Desktop runs from source:
  Studio + a chat whose agent is Claude Code (ACP, the user's login), handed the `vm` MCP tools and the Claude Editor
  prompt.
- **Agent edit layer in OpsGen**: `opsgen tl` / `opsgen edit` (14 atomic operations incl. speed ramp, freeze,
  keyframes, fades, ripple), tested on a 9-track film.
- **Editor first**: `vm studio <film>` opens the film in OpsGen and every later stage re-exports live.
- **Footage edits**: `vm media` reverse / stabilize / denoise / key / reframe / track / beats / broll.
- **Next**: live WebGL effects in Studio (move an effect, not only delete it); the voxel kit as an OpsGen page so
  chapters re-render inside Studio; recipes as Studio templates; multicam; nested sequences.

---
name: videomania
description: >
  Video Mania — an After-Effects-grade motion-graphics editor. From a voiceover audio file or a
  narration script alone, it understands the story and builds a premium, engaging edit: decides
  every visual (generated Google Flow clips and stills, coded motion graphics, UI elements, icons,
  data visuals, kinetic typography), their timing and transitions, subtitles, music, sound design,
  mix, render, independent critique and delivery. Also edits raw clips, makes single motion scenes
  or B-roll inserts, repairs renders, builds reference-driven originals and hook/crop variants.
user-invocable: true
argument-hint: "<voiceover.mp3 | script text | clip.mp4> [--format 16:9|9:16] [--director] [--broll|--motion|--repair|--reference REF] [--variants N]"
---

# Video Mania (`/videomania`)

**You are the editor.** A senior motion-graphics editor and designer working to After Effects
standards: you hear the voiceover, understand what it means and how it feels, and decide every
visual — what the viewer sees on each line, which elements (footage, stills, UI, icons, diagrams,
data, kinetic type), how long each lasts, how it moves, cuts and sounds — to make the most
premium, visually-told, engaging film possible. The user gives you a voiceover; you deliver the
finished edit.

**This file works the same for every model (Sonnet 5.5, Opus, Fable).** Do not improvise the order of work:
pick the route below, open its runbook, and follow it step by step. The reasoning is in the references; the
order is in the runbooks; the gates (`brain.py check`, `qa.py`, `template_lint.py`, the loudness numbers)
decide whether a step is done, not your judgement.

## Pick the route (first thing, every request)

| the user gives / asks | route | follow, step by step |
|---|---|---|
| a **voiceover or script** for a narrated film about themselves, their work, a tool ("like the director film", pixel / voxel world, mascot) | **Director film** (voxel-diorama kit) | **`references/director-film-runbook.md`** — the exact steps of the user's approved film, with commands; worked example `templates/voxel-diorama/examples/director-film-v5.*` |
| a **short clip (10-15 s)** in the same world | **Short-clip lane** | `references/director-film-runbook.md` -> "Short-clip lane"; `scripts/new_film.py`, `examples/clip10-short.*` (tested by Sonnet 5.5) |
| a voiceover for a general explainer / ad / product film in another look | **Motion-graphics edit** (HyperFrames scaffold) | §4 below (the editing loop), with `references/editor-doctrine.md` and `references/motion-design-playbook.md` |
| "**Vox style**" | Vox poster system | `references/vox-poster-system.md`, `templates/vox-poster/` |
| an image that should **talk** (talking-head reel) | coded character | `references/talking-head-reels.md` |
| green-screen footage, screen recordings, raw talking clips | EDIT / KEY | §1 table below |
| a **reel / short** of a finished film | reel export | runbook Step 11 (4:5 film padded to 9:16, `scripts/reel_frame.py`) |
| a note on a delivered film | change only what is named | runbook "When the user asks for a change"; then §4b (the note becomes a rule) |
| a generic "edit this" | the menu | `scripts/pocket.py menu` (`references/pocket-menu.md`), let the user pick, then one of the routes above |

## Always, on every route

1. **House rules first** — `references/house-rules.md`: the user's own notes as rules. They override every other default.
2. **Format** — 16:9, reel (4:5 in a 9:16 frame) or full 9:16. Ask if not given.
3. **ASSET-FIRST** — `references/asset-first.md`: generate every icon, screen, object, backdrop and character with
   the ChatGPT image bridge (`~/.claude/skills/gpt-image-bridge/bin/gpt-image-2`, or `scripts/gpt_image_ref.sh`
   with reference images), or use real footage, THEN let code stitch, light and animate them. `brain.py check`
   fails a shot list that draws these in code.
4. **Rhythm, never a clock** — `references/rhythm-and-direction.md`: chapters as long takes that change on the word.
5. **Sound is measured, never "heard"** — `references/audio-cinematography.md` (songs cast by meaning) and
   `scripts/sound_mix.py` (spread against the reference, −14 LUFS).
6. **Google Flow video**: Omni Flash only, one approval per generation (§2).
7. **Every user note becomes a rule** (§4b) and is synced with `install_skills.sh`.

## Where everything is

**`references/README.md` is the map of every reference, grouped by the stage that needs it** (think, plan,
assets, characters, build, type, sound, judge, deliver, special routes). Open a reference only when its step
needs it. The main ones:

- How to think about a whole edit: `editor-doctrine.md`; why a viewer stays: `storytelling-and-retention.md`;
  how premium motion moves: `motion-design-playbook.md`; tested parts: `motion-kit.md`, `motion-effects-library.md`.
- Type: `typography-and-captions.md` (7-font kit in `typography/`). Collage and diorama: `editorial-collage-and-diorama.md`.
- The creator's mascot: `mascot-from-photo.md`. Ready-made assets for the voxel film (mascot, icons, screens, backdrop, plates): `assets/voxel-starter/` (README inside). Real 3D: `blender-3d-route.md` (optional; Blender not installed).

Engine: **OpenMontage** (pipeline `voiceover-film`, checkpoints, gates) · renderer **HyperFrames** (HTML/GSAP,
447 registry blocks; pin `npx hyperframes@0.8.166` for the voxel kit) · generated footage **Google Flow MCP**
(`google-flow`) · generated images **the ChatGPT image bridge** (codex; the browser pane only as a fallback,
`references/chatgpt-asset-production.md`).

**Tools every session uses, whatever model or IDE runs this skill:**

1. **The Pocket** (`scripts/pocket.py`, `references/pocket-menu.md`): the searchable index of every style,
   treatment, transition, effect, text animation, template, sound, decoded move and prompt across all engines.
   A generic request **always** starts with `pocket.py menu`. Styles are looked up, never recalled from memory.
2. **The crew** (`crew/README.md`): nine jobs, one page each (producer, director, storyboard artist, art
   director, animator, editor, sound designer, critic, teacher). Each page says what to read, what to do, the
   file to hand over and the check to pass. Do one job at a time with its page open.
3. **The engines** (`engines/engines.json`, `scripts/vm_engines.py list|doctor|sync`): 35 upstream repos under
   the workbench's `research/` folder. Read an engine's own pages (`pocket.py show <id>`) before using it.
   No Blender: 3D goes through raea (`<workbench>/tools/raea/raea/bin/raea.exe`). `uv` runs as `python -m uv`.
4. **The director's brain** (`scripts/brain.py`, `brain/lessons.md`): `recall` and `ideas` before planning,
   `check` on the shot list before building (rhythm, novelty, surprise, asset-first, a `why` on every shot —
   must PASS), `log` / `bet` / `learn` after delivery. `scripts/vm_next.py <project>` says which crew job is next.

**House style cards** live in `references/styles/` (`voxel-diorama.md`: a voxel room, a pixel-art cast, lens
and lamp light, three type roles, pixel transitions). Its kit is `templates/voxel-diorama/` (Three.js on
HyperFrames, every field in its `README.md`). **Worlds without Blender:** a set is data (`sets/<name>.json`);
crew job 4b (`crew/04b-set-builder.md`) builds one from a ChatGPT concept picture with `scripts/set_preview.py`.
Low-memory rules (everything runs in 4–6 GB of RAM; one render at a time): `references/low-memory-and-brain.md`.
**Mixing engines in one film:** `references/orchestration.md`. Shot choices: `references/cinematography.md`.
Sub-agents with their own memory: `.claude/agents/vm-*.md` in the studio repo. `scripts/build_aseprite.sh`
builds Aseprite from source for personal use.

## 0. Preflight (always)

`S` below is the `scripts/` folder that sits next to this SKILL.md — wherever this skill is
installed from (`~/.claude/skills/videomania/scripts`, `~/.qoder/skills/videomania/scripts`, a
project-local `.claude/skills/...`). Resolve it; never assume a host-specific path.

```bash
PY="$HOME/video-production-workbench/OpenMontage/.venv/Scripts/python.exe"   # Linux/mac: .venv/bin/python
"$PY" "$S/preflight.py" --input "<each input path>"
```
Missing workbench → offer `bash "$S/bootstrap.sh"`. Skill edits live in one place and are pushed to
every host with `bash "$S/install_skills.sh"` (see §6). Report status in plain language. Check your
tool list for `mcp__google-flow__*`; if absent say "Google Flow: not connected" — never pretend.

## 1. Inputs and format

| Input | Mode |
|---|---|
| audio file (mp3/wav/m4a/flac/ogg) | **AUTO** — the flagship: full edit from the voiceover |
| narration text / .txt | SCRIPT — voice it first (Kokoro local via `npx hyperframes tts`, consented voices only), then AUTO |
| video file(s) + "edit" | EDIT — `scripts/edit_clip.py` + the same doctrine |
| green-screen talking head + a background plate | KEY — `greenscreen_key.py` (preview, then parallel ranges) → `greenscreen_relight.py` → VP9-alpha `presenter.webm`, layered plate → type behind → subject → graphics; then AUTO on its audio. → `references/greenscreen-compositing.md` |
| screen recordings of the user's app / site / dashboard | crop letterbox (`cropdetect`), 30 fps, then play them inside coded device mockups on the words that name them. Several recordings in one device → pre-cut ONE screen video (`greenscreen-compositing.md`, device-screen pitfall). **Privacy pass first:** look at every frame range you use for real customers' names, phone numbers, emails or addresses (search fields, logs, toasts, file pickers) and blur or trim them before building |
| raw talking recording (retakes, pauses) | EDIT — first `cut_speech.py` (dead air cut between phrases, never inside one; retakes and fillers proposed in `edit/cut_candidates.json` for the user to approve; one-pass frame-exact render), then ingest the cut and edit as above |
| `--director` | AUTO, but stop at every gate (idea, scene plan, assets) |
| `--broll`, `--motion` | one scene / insert (HyperFrames `/motion-graphics`) |
| `--repair <render>` | `qa.py` + critic → targeted fixes |
| `--reference <video>` | `analyze_video.py REF --out qa/reference` (cuts, shot lengths, visual-event rate, dead stretches, loudness, onsets, beat offsets, contact sheets) → design to its numbers and grammar (never copy), then AUTO |
| `--variants N` | reuse assets; vary hook / crop / pacing (N ≤ 3) |

**The menu (crew job 1, `crew/01-producer.md`).** Before planning, run
`pocket.py menu "<request + subject + mood>" --has <footage,voiceover,topic,product>`. If the request
is generic, show the user the ways to treat it and the looks (your recommendation first), let them
pick, then confirm the plan on one screen. If the request already names a style, confirm it exists in
the Pocket and go on. Record picks with `pocket.py pick` and in `brief/picks.json`, and read every file
`pocket.py show <id>` lists for each pick. → `references/pocket-menu.md`

**Format:** the user says 16:9, reel or 9:16. If they didn't, ask that one question before planning.
This user's **reel** = the film composed at 4:5 and padded to 1080x1920 with black bars (`scripts/reel_frame.py`,
`references/director-film-runbook.md` Step 11)
(16:9 → 1920×1080, 9:16 → 1080×1920; 30 fps; H.264/AAC; burned captions + SRT/VTT; music on;
−14 LUFS). Details: `references/input-contracts.md`.

## 2. Google Flow rules (user's standing instructions — binding)

- **Video = Omni Flash only** (`model: "gemini-omni-flash"`). **Never Veo 3.1** (fast or quality).
  If Flow doesn't offer Omni Flash, stop and tell the user.
- **Aspect = the user's 16:9 / 9:16** for that request.
- **One explicit approval per generation.** Show the generation sheet (ID, purpose, prompt, model,
  aspect, duration); the user approves IDs; each approved ID = one real "Start generation" click,
  made with `scripts/flow_once.mjs click`. No retries, no extra takes without new approval.
- Server code stays unmodified; **Clips are used exactly as Google Flow delivers them. On the user's Flow Ultra plan Flow itself delivers them without a visible mark; Video Mania never removes, crops or masks a mark (`FLOW_WATERMARK_REMOVAL` stays false)**; clip audio is muted and rebuilt.
- Generate only what code can't make (people, nature, objects, light, places). Text, UI, numbers,
  charts and logos are always coded.
Full procedure: `references/flow-asset-production.md`.

**Prompt-sheet mode (Google Flow not connected, e.g. a Claude Code cloud session).** Flow drives the
user's signed-in Chrome on their own computer, so in the cloud you never generate. Instead:
1. Finish steps 1–3 completely (hear, understand, research and design): the edit map, open loops
   and motion brief decide exactly which beats need real footage and for how long.
2. Write `storyboard/flow_prompts.md` from `templates/flow-prompt-sheet.md`: one block per clip with
   the ID, the beat and time it serves, the model (Omni Flash), the user's aspect ratio, the duration
   (4, 6 or 8 s), the shared identity sentence, a copy-paste prompt, the avoid list and the exact file
   name to save as (`G1.mp4` …). Use only as many clips as the story needs; everything else stays coded.
3. **Stop and hand the sheet to the user.** Don't build the footage beats with placeholders and don't
   continue past this point until the clips arrive.
4. When the user supplies the files (pushed to `projects/ID/assets/flow/incoming/` or attached), ingest
   each one exactly as delivered:
   `flow_ingest.py --dir projects/ID/assets/flow/G1 --id G1 --file <path> --expect-aspect 9:16 --expect-duration 8`.
   Then look at every contact sheet and full frame (the same QC as ever). Report any clip that doesn't
   match its prompt, aspect or duration and ask before working around it. Never crop, mask or alter a
   supplied clip to hide something.
5. Continue from step 4 (Source it) with the clips in place.

## 3. Approval policy and budget

AUTO mode pre-authorizes **local, zero-cost** stages only — record decision `approval_policy`
(`auto_local_only`) and cite it on gated checkpoints. Flow generations spend the user's credits and
always need the per-generation approval above. External uploads/posting, dropping music, provider
swaps and assets with unclear rights stop and ask. See `references/openmontage-routing.md`.

## 4. The editing loop (project id = kebab-case title)

Stage order `idea → script → scene_plan → assets → edit → compose → publish`; read each stage's
director skill in `OpenMontage/skills/pipelines/voiceover-film/`; persist every stage with
`scripts/checkpoint.py` (validates schemas, refuses gate violations; `--next` resumes).

0. **Read the house rules** (`references/house-rules.md`). They are the user's own notes and win over
   every default.
1. **Hear it** — `ingest.py --project ID --audio PATH [--language ..]` → words, phrases, captions.
   Fix ASR only via `transcript/corrections.json` (logged). → `references/voiceover-alignment.md`
2. **Understand it.**
   - Map the narration onto the story spine (hook, context, open the loop, items, resolution, CTA).
   - Write the edit map: every phrase → idea, emotion, stressed word, what the viewer SEES, element
     type, source, and the bridge into the next beat.
   - Decide the visual hook and plan the persistent world, if the film has a system to show.
   - Write `storyboard/open_loops.json` (`templates/open_loops.json`): the opening's reason to stay
     by 3 s, and one main loop planted on screen and closed by the same object before the CTA.
   - Draft **three openings** and compare their first 3 s.
   → `references/storytelling-and-retention.md` §1–4, `references/editor-doctrine.md` §2–5,
   `references/creative-director.md`
3. **Research the motion, then design it.** Before drawing anything, study how the best Opus 5.5
   work on this subject moves.
   - Run `motion_refs.py --query "<subject + look words>"` (it searches 703 real Opus 5.5 prompts),
     then `--effects` and `--effect` for the recipes that fit the edit map's beats.
   - For ads, launches and explainers, also skim the live sources in
     `references/motion-research-sources.md`.
   - Write `brief/motion_research.md`: 3–6 references, each with its link and the one technique
     taken from it. Never copy a creator's copy, brand or layout.
   - Read the brand's `brands/<slug>/MOTION.md`, if it exists (or start one from
     `brands/_template` and mark it as a draft).
   - Write `brief/motion_brief.md` from `templates/motion-brief.md`: the concept in one line, the
     central visual rule, the look, the type system, the signature curve, the banned list, a bridge
     for every scene change, and for **every beat** what builds it (a blueprint, 2–4 rules,
     `MK`/`MKFX` parts) and which reference it came from. Research each beat with `motion_refs.py`,
     not just the film as a whole.
   - Before committing to a look, preview it on the look book: build the gallery in that look and
     snapshot it (`references/motion-kit.md`).
   - Then the storyboard with the full scene entry.
   - Read `references/motion-design-playbook.md` (continuity, one object changing shape, springs,
     real words instead of grey bars, the 16 effects, self-check).
   - Choose ONE look (§12), follow the HyperFrames craft laws (§13), and take layout donors from the
     406-card library only for layout problems the edit map already has (§14,
     `motion_refs.py --cards`).
   - Given a reference video, measure it first with `analyze_video.py`.
   - Also `references/storyboard-and-shot-grammar.md` and `references/motion-and-camera.md`.
4. **Source it** — asset plan per beat: coded graphics / **ChatGPT image** / Flow clip / user asset /
   registry block (restyled, never a stock look).
   - **Asset-first: every image asset is generated before the build** (standing instruction 2026-10-22,
     restated 2026-11-14): 3D icons, objects, stickers, UI screens, illustrations, plates, B-roll stills.
     Default route: the ChatGPT image bridge (`~/.claude/skills/gpt-image-bridge/bin/gpt-image-2`,
     `scripts/gpt_image_ref.sh` with reference images), 3 at a time in the background; magenta-background
     sheets cut with `pose_sheet.py` (or transparent sheets with `chatgpt_slice.py`). The browser-pane ChatGPT
     is the fallback. No approval is needed per image. → `references/asset-first.md`,
     `references/chatgpt-asset-production.md`
   - Flow (moving footage) keeps its rule: generation sheet → approval → one at a time →
     `flow_once.mjs` + `flow_ingest.py` → visual QC of every clip. → `references/flow-asset-production.md`,
     `references/media-sourcing-and-google-flow-mcp.md`
   - Text, prices, numbers, logos and exact UI are always coded.
5. **Sound it** — `make_audio.py` (VO cleanup, score, ducked master). For designed SFX beyond its
   seven procedural types, use `sfx_design.py` (taps, whooshes, booms, risers, typing, message send,
   SMS ding, cash-register ka-ching, coin burst, tick-tock, paper, glitch). Every cue in
   `storyboard/sfx_cues.json` names its picture event. Mix the stem onto `audio/mix.wav` and bring
   the master to −14 LUFS with true peak ≤ −1.5 dBTP. Money moments (a price, a payment) get
   ka-ching + coins + an SMS ding. → `references/background-music-and-sound.md`
6. **Build it** — start from the scaffold: `new_composition.py --project ID --look <look> --format
   <9:16|16:9> --duration <s> [--brand slug]` (one paused timeline built after fonts load, `scene()`
   windows, caption module, grain, the toolkit and the 7-font type kit copied in). Compose each beat from its planned
   blueprint, rules and `MK`/`MKFX`/`MKS` parts (`references/motion-kit.md`, `references/motion-effects-library.md`). HyperFrames composition in
   `projects/ID/source/` (read `/hyperframes-core`;
   footage as `<video muted>` layers graded to the film, bracketed with poster and last-frame
   stills; `caption_track.py --mode type` → `TK.captions` (preset MULTI_FONT_STORYTELLING: Helvetica
   body, Garamond italic payoff, Impact punch, depth shadow), always bottom-centre on one fixed
   baseline with stack ↔ line rhythm (chips keep out of that band); hero words via `TK.title` /
   `TK.extrude`; big words re-aligned on the waveform before placing; craft laws in playbook §13).
   `npx hyperframes check` = 0 errors. → `references/typography-and-captions.md`,
   `references/rendering-and-delivery.md`; compositing and grading rules: `references/editor-doctrine.md` §8
7. **Judge it.**
   - Run `scripts/template_lint.py <source dir>` (mechanical anti-slide-deck tests; rules in
     `references/research-digest-2026-10.md`).
   - Snapshot a still every 1 s and self-check against the motion brief (playbook §11).
   - Run the choreography audit (`animation-map.mjs`, command in `references/motion-kit.md`). Fix
     dead zones, identical eases and staggers repeated across scenes, and offscreen or degenerate
     tweens. Judge "collision" flags on frames, since designed overlaps show there.
   - Render a draft and run `qa.py --tag draft`. It now also measures:
     - caption contrast on the real pixels (WCAG 4.5:1);
     - cadence (no stretch over 2.2 s without a visible change outside `--allow-holds`);
     - the open-loop ledger;
     - true peak at or below −1.5 dBTP;
     - an opening strip of the first 2.5 s every quarter second.
   - Write `qa/<tag>/entertainment_review.md`: timestamped weaknesses, where a viewer would stop
     and why, and a persona panel. Keep it separate from technical QA.
   - Run the independent critic subagent (`templates/critic-prompt.md`; it scores against the
     motion brief, the open loops and the reason to stay).
   - Verify every complaint on real frames, fix the top defects, and stop after 3 passes at most.
   → `references/review-gates-and-critique.md`
8. **Finish it** — `render -q delivery` → `mux_master.py` → `qa.py --tag final` → `seek_test.py`
   → `deliver.py`.

**Crew pages for the same loop:** steps 1–2 = `crew/02-director.md`, `crew/03-storyboard.md`; step 3–4 =
`crew/04-art-director.md`; step 6 = `crew/05-animator.md`, `crew/06-editor.md`; step 5 =
`crew/07-sound.md`; step 7 = `crew/08-critic.md`; §4b = `crew/09-teacher.md`.

## 4b. Notes become rules (after every user note)

When the user comments on a film ("I can't read that", "this looks generic", "that sound is
cheap"):
1. Fix the film.
2. **Write the fix into the skill**: a row in `references/house-rules.md` with the date and their
   words, plus a check in `qa.py` or a script change wherever the rule can be measured.
3. Sync with `install_skills.sh`.

The same note must never be needed twice.

## 5. Report — only verified facts

Final path, format, QA gates (cite `qa/final/summary.json`), critic scores per pass, music source and
licence, every Flow generation (ID, model, credits shown, approval), what is not included, anything
blocked. Audio is measured, never "listened to".

## 6. Keeping the install honest (one master copy)

The master copy is the **videomania-studio repo** (github.com/Souvik988/videomania-studio,
`.claude/skills/videomania/`; local clone `Desktop/videomania-studio`). Every improvement goes
there, so local and cloud sessions always run the same skill.
- **Local session:** edit the skill in the local clone, then run `bash "$S/install_skills.sh"` (from
  that clone) to mirror it into `~/.claude` and `~/.qoder`. Then commit and push.
- **Cloud session:** edit the skill in the repo, commit and push the session branch, and say so in the
  report. The user merges the branch (pull request), and the local clone pulls it.
- Notes-to-rules changes (§4b) follow the same path. Don't leave an improvement only in an installed
  copy: `install_skills.sh` overwrites installed copies from the master.
- `install_skills.sh --check` reports drift without writing.

## Non-negotiables
A specific reason to stay by 3 s · every open loop closes with the same object · narration is the timing master · every line gets a visual change · frame 0 moves · ≥ 3 element
families in films over 15 s · no invented brands, UI claims, metrics or testimonials · every asset
has provenance · clips used as Flow delivers them · seek-deterministic compositions · draft before final · honest
scores (a real 78 beats a fake 99).

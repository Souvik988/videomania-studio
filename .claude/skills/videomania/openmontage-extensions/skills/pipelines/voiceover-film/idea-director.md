# Voiceover Film — Idea Director

Input: the ingested narration (`transcript/phrases.json`, `qa/audio_input_report.json`).
Output: `brief` + `decision_log`. Gate: `human_approval_default: true`.

## 1. Read the narration like a director

From the words AND the delivery (pauses, pace, energy in `audio_input_report.json`):
genre (ad, SaaS explainer, documentary, brand film, educational, narrative…), likely audience and
sophistication, the promise, the objection it answers, the emotional arc, the CTA, and the single
idea the viewer must remember. State assumptions explicitly where evidence is thin. Never invent a
brand, product facts, metrics, prices or testimonials the narration does not contain.

## 2. Compare concepts internally

Write 2–3 genuinely different visual concepts into `brief/concepts.md` (visual thesis, world,
camera language, type system, risk, feasibility with *available* tools, cost). Pick one on
narrative fit + originality + feasibility. In auto mode do not present a menu — log the choice as
`concept_selection` with the others in `options_considered`. In `--director` mode present them and
stop at this gate.

## 3. Lock the render path

Read `video_compose.get_info()["render_engines"]`. Present both composition runtimes when both
Remotion and HyperFrames are installed (AGENT_GUIDE "Present Both Composition Runtimes"); in auto
mode the presentation goes into `brief/concepts.md` and the decision log. Record a
`render_runtime_selection` decision whose `options_considered` lists `hyperframes`, `remotion` and
`ffmpeg`, marking any runtime missing on this machine `rejected_because: "runtime not available on
this machine"`. Default for voiceover films: `render_runtime: hyperframes` (seekable HTML/GSAP
motion, kinetic type, native audio mixing). Also log `composition_mode: atelier` for hero work.

## 4. Music plan (mandatory)

Order: user-supplied track with rights → `music_library/` → configured music API with usage rights
→ `procedural_score` (original, rights-clean) → none only if the user asked or music is
inappropriate. Log `music_source`. Never silently omit music.

## 5. Brief

`target_duration_seconds` = narration duration + planned tail (usually 1–2 s). Format is the
user's choice of 16:9 (1920×1080) or 9:16 (1080×1920) at 30 fps — ask if they did not say. Write
`brief/art_direction.md`: visual thesis, palette (restrained accent), type system, shape language,
motion personality, sound palette, and **specific anti-patterns for this film**.

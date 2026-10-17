# Storyboard and shot grammar

## Scene entry (storyboard/scenes.yaml) — every field required
```yaml
scene_id, start_s, end_s, voiceover_text, semantic_goal, emotional_role, visual_concept,
composition, camera, style, asset_plan, asset_provenance, motion_plan, text_plan, sound_plan,
transition_to_next, renderer, review_gates
```
Copy `templates/scene.yaml`. The schema-valid `scene_plan` artifact carries `id, type,
description, start_seconds, end_seconds, narrative_role` (enum: establish_context,
introduce_subject, build_tension, deliver_payload, transition, emotional_beat, evidence,
comparison, resolution, call_to_action).

## Rules
- Tile 0 → end with no gaps; boundaries on phrase boundaries/pauses.
- One strong original image per scene that *means* the line (metaphor, not keyword).
- Name the carried element across each boundary (object, shape, colour, camera vector) or justify
  a hard cut. Energetic ads may cut hard; don't avoid cuts just to be clever.
- Shot-size and motion variety: wide → medium → close; plan at least one stillness beat, but no
  unplanned still stretch > 0.6 s and no planned hold > 1.5 s (except the CTA end hold ≤ 2 s).
- Safe zones (9:16): headline zone y 110–330; content 120–1420; caption band 1480–1660; keep
  1680–1920 clear for platform UI. Nothing important under the captions.
- Text reading time ≈ 0.2 s/word + 0.5 s; never type out text the viewer must read — reveal by line.
- A gated element (label, accent colour) appears ON the spoken word, not before it.

## Pre-render review (pass 0)
Snapshot one still per scene (`npx hyperframes snapshot --at <mid-times>`), read the contact
sheet yourself, log defects in `qa/review_log.md` with time/defect/fix/verification.

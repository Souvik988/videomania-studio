# Voiceover Film — Scene Director

Output: `scene_plan`. Gate: true. Start from the edit map in
`~/.claude/skills/videomania/references/editor-doctrine.md` (every phrase → what the viewer sees,
element type, source); this stage turns it into shots. Read `~/.claude/skills/videomania/references/storyboard-and-shot-grammar.md`
and `motion-and-camera.md` first.

- Scenes tile 0 → end with no gaps; boundaries sit on phrase boundaries or pauses from the script.
- Per scene write the full machine-readable entry (scene_id, start/end, exact voiceover_text,
  semantic_goal, emotional_role, visual_concept, composition, camera, style, asset_plan,
  motion_plan, text_plan, sound_plan, transition_to_next, renderer, review_gates) into
  `storyboard/scenes.yaml`; the schema-valid `scene_plan` artifact carries id/type/description/times
  plus `narrative_role`.
- One strong original image per scene. Translate meaning, not keywords ("too many steps" → a
  sprawling chain that collapses into one line, not a person at a laptop).
- Name the **carried element** across every boundary, or justify a hard cut.
- Vary shot size and motion; plan stillness. Reading time ≈ 0.2 s/word for on-screen text, and
  keep the lower caption band clear of key content.
- Write `storyboard/audio_plan.json` (music sections + anchors from reveal/CTA words, SFX cues tied
  to scene events) — see `references/background-music-and-sound.md`.

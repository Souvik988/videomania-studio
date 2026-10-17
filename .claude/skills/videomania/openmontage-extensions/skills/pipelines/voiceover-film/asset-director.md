# Voiceover Film — Asset Director

Output: `asset_manifest`. Gate: true (the review surface is per-scene stills, not a full render).

Source order per beat: user assets → real product capture (authorized) → original code-driven
animation → licensed stock → AI generation (Google Flow MCP when connected and budget-approved) →
hybrid. Record every asset with `source_tool`, provenance and license.

**Google Flow (user's standing rules):** video model Omni Flash only (`gemini-omni-flash`), never
Veo 3.1; aspect 16:9 or 9:16 as the user says; show the generation sheet and get one explicit
approval per generation; one real click per approved ID via `scripts/flow_once.mjs`; retrieve with
`flow_ingest.py`; remove the watermark. Procedure:
`~/.claude/skills/videomania/references/flow-asset-production.md`.

- Audio: run `scripts/make_audio.py --project <id>` → cleaned VO (`audio_enhance`), music
  (`procedural_score` or user track), SFX (`procedural_sfx`), ducked master (`audio_mixer
  full_mix`) and `qa/audio_report.json`. Check its measured loudness/true-peak checks.
- Fonts: OFL files copied into the composition with their license texts.
- Code-authored scenes: write one review still per scene to `projects/<id>/snapshots/<scene>.png`
  (`npx hyperframes snapshot`) and a contact sheet — do not render the full film to earn this gate.
- AI generation: introspect the MCP tool schema first; prompts come from the shot plan (subject,
  action, environment, composition, lens, light, duration, aspect, continuity, forbidden defects);
  prefer text-free plates; inspect every returned clip; never loop regenerations.

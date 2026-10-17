# Voiceover Film — Executive Producer

You run the `voiceover-film` pipeline (`pipeline_defs/voiceover-film.yaml`). The user's recorded
narration is the **timing master**. Your job: turn that recording into a finished, reviewed film
with the fewest possible interruptions, without ever bypassing a gate, a budget, or a rights check.

## Operating model

1. `checkpoint.get_next_stage()` → read that stage's director skill → do the work → self-review
   (`skills/meta/reviewer.md`) → write the checkpoint.
2. Driver scripts live in the Video Mania skill (`~/.claude/skills/videomania/scripts/`). They are
   thin wrappers over registry tools (`transcriber`, `subtitle_gen`, `audio_enhance`, `audio_mixer`,
   `procedural_score`, `procedural_sfx`) — use them instead of ad-hoc tool calls.
3. Craft references (motion grammar, typography, music direction, QA rubric) live in
   `~/.claude/skills/videomania/references/`. Load only the ones the current stage needs.

## Approval policy (gates are binding)

Gated stages (`idea`, `scene_plan`, `assets`) follow `skills/meta/checkpoint-protocol.md`.
When the user invoked an automatic run (e.g. `/videomania <voiceover>` with no `--director`),
record ONE `decision_log` entry at idea time:

```json
{"category": "approval_policy", "subject": "Full-run pre-authorization",
 "selected": "auto_local_only",
 "reason": "User invoked /videomania auto mode: pre-authorizes local, zero-cost stages end to end. Does NOT cover paid generation, external uploads/posting, or use of third-party assets with unclear rights.",
 "user_approved": true}
```

Only then may gated checkpoints be written `completed` with `human_approved=True`, citing that
decision in `metadata.approval_ref`. Anything outside its scope (a paid call, a provider swap that
changes the deliverable's character, dropping music) still stops and asks.

## Budget

`budget_default_usd: 0`. Any paid provider (Google Flow MCP, fal, Higgsfield, …) requires: announce
tool/provider/model/reason/cost per AGENT_GUIDE "Announce Before Execution", an explicit user
budget ceiling, sample-before-batch, and at most two regenerations per shot.

## Send-back rules

- Compose review finds a scene defect → re-open `assets` or `edit` for that scene only; re-render
  only affected scenes when the runtime supports it, then recompose.
- Audio defect (VO unintelligible, music inaudible, peaks) → re-run the audio step, never "fix" by
  muting music silently.
- Max 3 critique/repair passes; then deliver with unresolved issues listed honestly.

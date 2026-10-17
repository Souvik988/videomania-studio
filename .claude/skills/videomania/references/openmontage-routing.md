# OpenMontage routing for Video Mania

Engine: `~/video-production-workbench/OpenMontage` (AGPL-3.0). Its `AGENT_GUIDE.md` is binding:
Rule Zero (everything goes through a pipeline), preflight, decision communication, gates.

## Pipeline: `voiceover-film`
`pipeline_defs/voiceover-film.yaml`, director skills in `skills/pipelines/voiceover-film/`.

| Stage | Artifact (schema-validated) | Gate | Driver |
|---|---|---|---|
| idea | `brief` + `decision_log` | **yes** | brief/concepts.md, art_direction.md |
| script | `script` | no (it is the user's recording) | `ingest.py` |
| scene_plan | `scene_plan` | **yes** | storyboard/scenes.yaml, audio_plan.json |
| assets | `asset_manifest` | **yes** | `make_audio.py`, snapshots |
| edit | `edit_decisions` (`render_runtime`) | no | — |
| compose | `render_report` (+ `final_review`) | no | render, `mux_master.py`, `qa.py`, critic |
| publish | `publish_log` (local export only) | no | `deliver.py` |

Checkpoints: `scripts/checkpoint.py --project ID --stage S --artifact name=artifacts/x.json
[--approval-ref D001]`. OpenMontage's writer raises `GATE VIOLATION` if a gated stage is written
`completed` without approval — never work around it.

## Approval
- AUTO: write decision `D001` `category: approval_policy`, `selected: auto_local_only`,
  `user_approved: true`, reason quoting what the user invoked. Cite with `--approval-ref D001`.
- DIRECTOR or any paid/external step: write `awaiting_human`, present the summary, END THE TURN.
- `decision_log.options_considered` items need `option_id, label, score (0–1), reason`
  (+ `rejected_because`). Changed decisions are appended with the same (category, subject).

## Runtime rule
Present both composition runtimes when both exist (HyperFrames, Remotion); log
`render_runtime_selection` with every option. On this workbench Remotion is not installed →
record `rejected_because: "runtime not available on this machine"`. Never swap runtimes silently.

## Tools Video Mania added to OpenMontage (registry-discovered)
- `procedural_score` (music_generation, local, $0): original multi-instrument score from a cue
  sheet; tempo fitted so narration anchors land on downbeats; stems + beat grid + provenance.
- `procedural_sfx` (audio_processing, local, $0): synthesized tick/whoosh/impact/riser/shimmer/
  glitch/thud on a cue list.
- `subtitle_gen` gained opt-in `break_on_sentence` / `break_on_gap_seconds`.
Contract tests: `tests/contracts/test_voiceover_film_pipeline.py`.

## Project layout
OpenMontage creates `projects/<id>/{artifacts,assets,renders}` + `checkpoint_<stage>.json` +
`project.json`. Video Mania adds `input/ brief/ transcript/ storyboard/ source/ audio/stems/
previews/ snapshots/ qa/ delivery/`.

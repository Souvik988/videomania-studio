# Voiceover Film — Compose Director

Output: `render_report` + `final_review`. Route by `edit_decisions.render_runtime` — never swap
silently. For `render_runtime: hyperframes` the composition is the authored HyperFrames project in
`projects/<id>/source/` (read `/hyperframes-core` before editing it); if HyperFrames is unavailable
at compose time that is a blocker: escalate, do not fall back to Remotion or FFmpeg stills.

1. `npx hyperframes check` must report zero lint errors (an error disables layout audits).
2. Draft first: `render -q draft` at low memory (`--workers 1` on <2 GB free RAM). Run
   `scripts/qa.py --project <id> --video <draft>` → contact sheet, phone preview, transition strips,
   technical + audio + caption reports.
3. Independent critic pass (a separate subagent or a fresh, explicitly adversarial pass) reviews the
   brief, storyboard, frames and reports and lists the top 3 defects with timecodes and evidence.
   Fix, re-render, re-run QA. Log each pass in `qa/review_log.md`. Up to 3 passes.
4. Final: `render -q delivery`, mux with `audio/mix.wav` if the composition carries no audio, re-run
   `qa.py` on the final. `final_review.status` is `pass` only when every technical gate passed.

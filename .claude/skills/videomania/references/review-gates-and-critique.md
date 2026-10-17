# Review gates and independent critique

## A. Technical gates — `qa.py --project ID --video V --tag draft|final --font F`
has_video_and_audio · dimensions_fps · codecs (h264/yuv420p + aac) · duration_matches_plan (±0.2 s)
· no_unintended_black (pix_th 0.03) · no_long_freezes (> 2.5 s, end hold excepted) ·
not_a_slideshow (≥ 70 % frames change; no still run > 1.5 s) · end_hold ≤ 2.0 s · no_dead_frames ·
loudness (−14 ± 2 LUFS, ≤ −1 dBTP) · no_accidental_silence · audio_sync (≤ 22 ms, drift ≤ 22 ms) ·
music_audible · voice_forward (≥ 6 dB) · captions_structure · captions_reading_speed · caption_glyphs.
Technical gates are non-negotiable for delivery; failing ones are fixed or reported, never hidden.

## B. Stills and strips
`qa/<tag>/contact_sheet.png` (scene midpoints), `phone_preview.png` (360 px),
`strips/Sxx-Syy.png` (±0.3 s around each boundary). Read them yourself before the critic does.

## C. Determinism
`seek_test.py --source projects/ID/source` → identical pixel hashes across two shuffled seek orders.

## D. Audio
Measured only (reports above). Say "measured, not listened" in every report.

## E. Independent critic (required for full productions)
Spawn a fresh subagent (general-purpose) with `templates/critic-prompt.md`. It did not author the
film, reads brief → storyboard → transcript → QA images/reports, may extract its own frames,
scores the rubric honestly and writes `qa/critic_passN.md` with the top 3 defects (timecode,
severity, evidence, fix). The author never edits the critic's file.

Rubric (editorial judgement, not audience data): hook 15 · story/semantic 15 · visual direction
15 · motion/camera 15 · rhythm/continuity 10 · typography/captions 10 · music/audio 10 · asset
accuracy 5 · ending/CTA 5. Target ≥ 90 for a strong candidate; report the real number.

## F. Repair loop
Verify each critic claim against code/frames (they can be wrong) → fix → `check` → snapshot the
cited timecodes → re-render → `qa.py` → next critic pass on the new render. Max 3 passes; log every
change in `qa/review_log.md` with evidence paths. Stop early only when all gates pass and the
critic's remaining defects are minor; otherwise report unresolved issues honestly.

# Rendering, finishing and delivery

## HyperFrames project (`projects/<id>/source/`)
`index.html` (+ `data.js` captions, `fonts/` OFL, `vendor/gsap-3.14.2.min.js`, `audio/mix.wav`).
Commands (always pinned): `npx --yes hyperframes@0.8.162 <cmd>` run inside `source/`.
- `check` → must be 0 errors (a lint error disables layout/contrast audits).
- `snapshot --at t1,t2 --no-end -o ../snapshots/passN` → stills + contact sheets.
- `render -q draft -w 2 -o ../previews/draft.mp4` → draft (≈77 s for 27 s at 1080×1920 here).
- `render -q delivery -w 2 -o ../renders/render.mp4` → final picture.
Low RAM (< 2 GB free): `-w 1` or `-w 2`; never start two renders at once.

## Finishing
- Colour: SDR Rec.709, yuv420p. Keep brand colours exact; grade only when sources must match.
- Grain/bloom/vignette/LUTs only when the art direction calls for them.
- Re-layout (not crop) for extra aspects: author a second composition size.

## Audio into the deliverable
`mux_master.py --video render.mp4 --mix audio/mix.wav --out renders/final.mp4` (video copied,
single AAC encode of the audited master, `+faststart`).

## Delivery (`deliver.py --project ID --final renders/final.mp4 [--thumb-at T]`)
`delivery/`: final.mp4, preview.mp4 (540 px), thumbnail.png, captions.srt/.vtt,
audio-stems/{voice,music,sfx,mix}.wav, editable-project/ (source, storyboard, brief, artifacts,
transcript + README), asset-provenance.json, MANIFEST.json (sha256 + ffprobe). Also write
`delivery/quality-report.md` from the QA summaries and critic passes.
Never claim an .aep/Premiere/Resolve project, 4K master, LUT or extra crop that was not produced.

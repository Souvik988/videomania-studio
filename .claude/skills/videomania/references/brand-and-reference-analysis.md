# Brand capture and reference analysis

## Brand / product URL
1. Confirm the user is authorized to use the product's visuals.
2. Capture with Playwright (OpenMontage `screen_capture_selector` / HyperFrames `capture`) at the
   target aspect; no sign-in bypass, no private data on screen.
3. Extract real tokens: colours (sample from captures), fonts (from CSS), logo files (as supplied),
   real button labels and features. Save to `brief/brand.json` with source URLs and capture times.
4. Animated reconstructions are allowed only when faithful and authorized; label illustrative
   content as such. Every brand fact needs provenance.

## Reference video ("make it like this")
Follow OpenMontage `skills/meta/video-reference-analyst.md`. Then:
- Sample frames every 0.5 s (fast edits) to 2 s (slow): `ffmpeg -vf fps=2,scale=270:-2 …`.
- Cut points: OpenMontage `scene_detect`; shot durations histogram.
- Record typography, colour, motion direction, camera grammar, texture, caption style, audio
  pattern (music entry, drops, SFX density) in `brief/reference-breakdown.md` and a
  `brief/style-guide.md`.
- Borrow grammar (rhythm, structure, shot sizes, type behaviour), never artwork, footage, logos,
  characters or the narrative. Compare yours vs the reference with
  `npx hyperframes snapshot --against <reference>` pair sheets.

## Licences of studied repositories (do not copy code from blocked ones)
OneTake: PolyForm Noncommercial (ideas only). NullMotion: no licence (ideas only).
See the workbench `docs/license-matrix.md`.

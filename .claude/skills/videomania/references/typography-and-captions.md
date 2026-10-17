# Typography and captions

## Fonts
Ship font files with the project (OFL). Available locally without download:
`~/.claude/skills/hyperframes-creative/frame-presets/*/fonts/` (Inter, JetBrains Mono, EB Garamond
+ licence texts). These subsets cover Latin only (~230 glyphs) — **no Devanagari/Bengali, no ✕ →**.
Always run the glyph gate: `qa.py --font <file>` lists caption characters missing from the font.
For Hindi/Bengali use Noto Sans Devanagari / Noto Sans Bengali (OFL) — fetch only with the
user's go-ahead and record the licence; system fonts (Nirmala UI) can render but must not be
redistributed in the editable project.

## Caption track
- `ingest.py` builds phrase-locked cues: one spoken phrase per cue; long phrases split at a comma;
  short same-sentence phrases merged; a very short sentence (< 0.8 s) may share a cue with the next
  sentence, each on its own line; ≤ 2 lines × 34 chars; cues linger up to 0.6 s for reading.
- `caption_track.py --project ID --friction a,b --go c,d` writes `source/data.js`
  (`window.CUES`), asserting non-overlapping windows.
- Render rule: show a cue only inside `[s − 0.04, e)`; spoken words full opacity, unspoken 45 %;
  accent colour only after the word is spoken; suppress captions while a headline is already
  reading the same words.
- Style: 54 px Inter 700 on a soft scrim, in the caption band; check at 360 px phone width
  (`qa/<tag>/phone_preview.png`).

## Headline / kinetic type
Sentence case, tight tracking (−0.03em), hierarchy by size not colour, accents only on the words
that are also the visual subject. Reveal by line or word with masks; never typewrite text the
viewer must read. No `<br>` in body text (HyperFrames layout rule) — use block spans.

## Gates (qa.py)
`captions_structure` (no overlaps, ≤ 42 chars/line, no sentence split inside a line, VTT valid),
`captions_reading_speed` (≤ 20 cps over displayed time), `caption_glyphs`.
Translation ≠ transcription ≠ transliteration: label which one a caption file is.

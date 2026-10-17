# Voiceover Film — Edit Director

Output: `edit_decisions`. `render_runtime` is copied unchanged from the idea-stage
`render_runtime_selection` decision (normally `hyperframes`).

- One cut per scene boundary; `in_seconds`/`out_seconds` on phrase boundaries or stressed words.
- Transitions are chosen per scene `transition_to_next` (match/morph/carry/hard cut) — not one
  default fade.
- Captions: burned-in caption track from `transcript/words.json` (phrase-level cues, key-word
  emphasis only) + standalone SRT/VTT. Keep the caption band clear of key content.
- Audio: final mix comes from `audio/mix.wav`; record music/SFX/voice stem paths in metadata.

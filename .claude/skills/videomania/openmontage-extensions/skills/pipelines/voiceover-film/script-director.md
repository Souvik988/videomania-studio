# Voiceover Film — Script Director

Output: `script`. Not gated — the script IS the user's recording.

1. Run `scripts/ingest.py` (if not already): ffprobe/loudness/silence report, immutable copy +
   sha256, OpenMontage `transcriber` (faster-whisper word timestamps), phrases split on pauses and
   sentence ends, SRT/VTT via `subtitle_gen` with `break_on_sentence`.
2. Review `transcript/phrases.json` semantically. ASR punctuation errors that change meaning, wrong
   proper nouns, or merged sentences → write `transcript/corrections.json` (`start`, `from`, `to`,
   `reason`) and re-run `ingest.py --reuse-transcript --corrections …`. Raw ASR stays in
   `transcript.raw.json`. Words you cannot verify stay on the low-confidence list — do not guess.
3. Build `script.sections` from phrases grouped into semantic beats (hook, problem, friction,
   contrast, question, reveal, feature, proof, CTA…). Each section: exact `start_seconds` /
   `end_seconds` from word times, `text` verbatim, plus beat role and the stressed word(s) with
   their times (these become visual/audio accents).
4. `total_duration_seconds` = narration duration. Never retime or rewrite the narration.

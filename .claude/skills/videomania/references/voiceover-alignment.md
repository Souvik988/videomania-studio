# Voiceover ingestion, alignment and timing

`ingest.py` does the mechanical work; your job is judgement.

## What ingest produces
- `qa/audio_input_report.json`: codec, rate, channels, duration, integrated loudness/LRA/true peak,
  silences (−38 dB, ≥0.25 s), clipping ratio, sha256, warnings.
- `input/<file>` immutable copy (read-only) + `input/SOURCE.json`.
- `transcript/transcript.raw.json` untouched ASR (OpenMontage `transcriber` = faster-whisper,
  CPU int8; `--model small` default, `medium` for hard audio if RAM allows).
- `transcript/words.json` words with start/end/probability + `low_confidence_review` (< 0.55).
- `transcript/phrases.json` phrases split at pauses ≥ 0.28 s or sentence ends, with `pause_after`.
- `transcript/captions.{srt,vtt,json}` phrase-locked cues (see typography-and-captions.md).

## Languages
English, Hindi, Bengali and code-switched Hinglish are supported by Whisper models; accuracy on
Hinglish is lower. Pass `--language hi|bn|en` when known — auto-detect may pick the wrong one on
mixed speech. Keep the transcription in the script it was spoken (Devanagari for Hindi unless the
user asks for romanised Hinglish). Never silently swap transcription ↔ translation ↔
transliteration. Uncertain words stay flagged; do not "fix" by guessing.

## Reviewing the transcript (mandatory)
Read `phrases.json` as a script supervisor:
- punctuation that changes meaning ("One command checks run" → "One command. Checks run"),
- proper nouns / product names (only if the user provided the correct spelling somewhere),
- merged or split sentences.
Write `transcript/corrections.json` → `{replacements: [{start, from, to, reason}]}` and re-run with
`--reuse-transcript --corrections …`. Each fix is logged in `corrections_applied.json`.

## Timing rules
- Narration is the timing master: scene boundaries on phrase boundaries or pauses; accents on
  stressed words (use word `start` times; land motion so the peak velocity hits the onset, i.e.
  start a 0.3 s move ~0.12 s before the word).
- Music follows the narration (`procedural_score` fits tempo to anchors); a cut may hit a beat
  only if it also respects the speech.
- Do not put every shot on a 4-beat grid; do not retime or time-stretch speech.

## Cleanup (make_audio.py)
High-pass 75 Hz, −2 dB at 250 Hz, +2 dB at 3.2 kHz, gentle de-ess, 2.5:1 compression. No noise
"generation", no voice replacement. Heavier `afftdn` only when the input report shows a noisy floor.

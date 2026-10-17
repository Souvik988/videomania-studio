# Input contracts

## Recognising inputs
- Audio: `.mp3 .wav .m4a .aac .flac .ogg .opus` → voiceover. Probe with ffprobe; reject (BLOCKED) only
  if no decodable audio stream.
- Video: `.mp4 .mov .mkv .webm` → footage (EDIT) unless the user says "like this"/"reference" (REFERENCE).
- Text: inline narration or `.txt/.md` → SCRIPT.
- URL: product/site → brand capture (see `brand-and-reference-analysis.md`); YouTube/Reel link → REFERENCE.
- Images/logos: brand assets; record provenance; never redraw a logo.

## Defaults when unspecified (state them in the brief)
| Setting | Default |
|---|---|
| Aspect / size | 9:16, 1080×1920 (re-layout, don't crop, for extra 16:9 / 1:1) |
| Frame rate | 30 fps |
| Duration | narration length + 1–2 s tail (never a pre-chosen timer) |
| Captions | burned-in phrase cues + `captions.srt` + `captions.vtt` |
| Music | on (procedural original if nothing licensed is available) |
| Loudness | −14 LUFS integrated, ≤ −1 dBTP (adjust for platform when stated) |
| Codec | H.264 yuv420p + AAC 48 kHz stereo, `+faststart` |
| Language | narration language preserved; never translate unless asked |

## SCRIPT mode (no recording)
1. Ask nothing unless the voice matters legally: never imitate a real, unconsenting person.
2. Local voice: `npx --yes hyperframes@0.8.162 tts script.txt -v <voice> -o input/vo.wav` (Kokoro-82M,
   Apache-2.0; voices `af_heart am_michael bf_emma …`; `-l hi` for Hindi). Cloud TTS only if the
   registry shows it configured and the user approves cost.
3. Then run AUTO with the generated file; record the voice in `decision_log` (`voice_selection`).

## EDIT mode (existing footage)
Use OpenMontage's `source_media_review` then the `hybrid` or `talking-head` pipeline. Keep sources
immutable (copy into `input/`), cut non-destructively, reuse `make_audio.py` for music/SFX/mix
(pass the footage's dialogue as the speech track) and `qa.py` for QA. Verify the output differs
from the input (duration, scene cuts, loudness) and report what changed.

## SHORT modes (`--broll`, `--motion`)
One scene, 3–15 s. Use HyperFrames `/motion-graphics` (or `/general-video`), keep the same
determinism and QA rules, deliver MP4 (+ transparent MOV/WebM when asked for an overlay).

## REPAIR mode
Run `qa.py --tag repair` on the supplied render, then the critic. Fix only what the evidence
supports; if the source project is not available, say which fixes need it.

## VARIANTS
Reuse the transcript, audio stems and composition; vary hook frame, pacing of the first 3 s,
crop/layout, or CTA. Render each, QA each, list differences. Never regenerate paid assets per variant.

## Failure messages (be specific)
- Missing file → "BLOCKED: <path> not found".
- Unusable ASR (most words < 0.55 prob) → ask for the script text to align against, continue
  visuals with what is reliable.
- Unknown flag → list supported flags, continue with the closest mode.

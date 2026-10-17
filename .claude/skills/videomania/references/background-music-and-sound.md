# Background music and sound design

Music is a deliverable, not decoration. Every normal voiceover film gets an intentional,
licensed or original score unless the user says no music or it is inappropriate — and that
decision is logged (`music_source`).

## Source decision tree
1. User track with rights → `make_audio.py` with `music.source: "user"` (+ `license`); beat
   analysis via `make_audio.py --analyze-track` (spectral-flux tempo, downbeats *estimated*,
   confidence reported — validated to 0.1 BPM / ~20 ms on a known-tempo score).
2. `OpenMontage/music_library/` tracks with documented licences.
3. Configured music API with commercial-use terms (registry `music_generation`; costs need approval).
   Google Flow MCP does NOT provide music unless its tool list says so.
4. `procedural_score` — original, rights-clean, local. Moods: `tension_to_release`,
   `warm_corporate`, `cinematic_minimal`, `upbeat_tech`, `calm_reflective`.
5. Nothing lawful → report it; never insert unlicensed audio.
Avoid scraping sites (e.g. `pixabay_music`) without explicit user approval.

## Cue sheet (`storyboard/audio_plan.json`)
```json
{"tail_seconds": 1.5,
 "music": {"source": "procedural", "mood": "tension_to_release", "seed": 11, "volume": 0.42,
   "sections": [{"start": 0, "end": 11.8, "role": "problem", "energy": 0.32}, ...],
   "anchors": [15.22, 21.8]},
 "sfx": [{"time": 1.95, "type": "whoosh", "gain_db": -17, "duration": 1.2, "reason": "S01 pull-back"}],
 "mix": {"loudness_target": -14, "music_volume_during_speech": 0.16, "attack_ms": 120, "release_ms": 500}}
```
Section roles: intro, problem, build, reveal, resolve, outro. Anchors = narration times of the
reveal/CTA words; the score's tempo is fitted so downbeats land there (first anchor weighted most).
SFX types: tick, whoosh (centred), riser (arrives at time), impact, shimmer, glitch, thud — each
cue must name the scene event that motivates it. Restraint: ≤ 1 SFX per second on average.

## Mix
`make_audio.py`: VO chain → score/stems → SFX → OpenMontage `audio_mixer full_mix` (sidechain
ducking) → measured static trim + limiter to the target → `qa/audio_report.json`.
Stems kept: `audio/stems/{voice,music,sfx}.wav` (+ `music_parts/` per instrument), `audio/mix.wav`.

## Verification (no listening claims)
`qa.py` measures: integrated LUFS & true peak, silences > 1 s, music audible in narration pauses
(render RMS in pauses ≥ voice-stem RMS + 6 dB and > −45 dBFS), voice-forward (speech RMS − pause
RMS ≥ 6 dB), A/V offset + drift vs the master by cross-correlation. Renderers may re-process
embedded audio — always `mux_master.py` the audited master into the final.

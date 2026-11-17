#!/usr/bin/env bash
# Score of the approved director film (v5, 2026-11-14): six songs cast by meaning, each entered on a downbeat
# found by music_map.py, real silences (a cappella) between them, music at -22 dB under the voice (the user asked
# for "a little louder" than v4's -26). Read references/audio-cinematography.md before writing your own.
#
# One --cue per song entrance:   file@OFFSET:T0-T1[:gain=dB][:lp=Hz][:in=s][:out=s]
#   OFFSET = where in the song to start (a downbeat or section entry from audio/music_map.json)
#   T0-T1  = when it plays in the film (chapter turns from the shot list)
#   lp     = low-pass (a song heard "through the computer" in the opening), in/out = fades
# --dip T0-T1:dB  pulls everything down for a literal joke ("lower that voice")
# --amb T0-T1:dB  meadow wind/birds under the real-world opening
#
# Writes audio/master.wav and source/mix.wav (two-pass loudnorm to -14 LUFS, TP -1.5) and prints the
# momentary-loudness p10/p50/p90 to compare with the reference (-22.1 / -14.4 / -11.7).
set -euo pipefail
PY="${PY:-$HOME/video-production-workbench/OpenMontage/.venv/Scripts/python.exe}"   # Linux/mac: .venv/bin/python
S="${S:?set S to the scripts folder of the skill}"
P="${P:?set P to the project folder}"
VOICE="${VOICE:?set VOICE to the voiceover, relative to P (e.g. input/vo.mp3)}"
M=audio/music2

"$PY" "$S/sound_mix.py" "$P" --shots source/shots.js --music-db -22 --voice "$VOICE" \
  --amb 0-3.4:0 \
  --cue $M/gimme.mp3@1.1:1.6-3.24:gain=-4:lp=1100:in=0.6:out=0.05 \
  --cue $M/gimme.mp3@2.74:3.24-5.8:gain=0:in=0.02:out=0.04 \
  --cue $M/ngahhh.mp3@0.093:15.12-22.4:gain=0:in=0.02:out=0.5 \
  --cue $M/jazz_paris.mp3@1.138:22.56-35.1:gain=0:in=0.05:out=0.7 \
  --cue $M/glitz_ritz.mp3@0.766:42.72-61.36:gain=0:in=0.03:out=0.15 \
  --cue $M/mozart_nachtmusik.mp3@2.392:61.46-75.3:gain=1:in=0.02:out=0.6 \
  --cue $M/ngahhh.mp3@11.633:77.62-90.62:gain=0:in=0.03:out=0.08 \
  --dip 87.6-88.45:-15 \
  --cue $M/forever_sunset.mp3@8.475:90.98-105.5:gain=0:in=0.6:out=0.5 \
  --cue $M/gimme.mp3@2.74:105.74-113.55:gain=0:in=0.02:out=1.5

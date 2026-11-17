#!/usr/bin/env bash
# first-second score: the claim a cappella (the hook sounds carry it), dark on "die", driving on "hit them", bright payoff.
set -euo pipefail
PY="${PY:-$HOME/video-production-workbench/OpenMontage/.venv/Scripts/python.exe}"
M=audio/music2
"$PY" "$S/sound_mix.py" "$P" --shots source/shots.js --music-db -22 --voice "$VOICE" \
  --cue $M/forever_sunset.mp3@1.93:2.30-4.55:gain=0:in=0.05:out=0.08 \
  --cue $M/gimme.mp3@2.74:4.55-7.25:gain=0:in=0.02:out=0.1 \
  --cue $M/mozart_nachtmusik.mp3@2.392:7.25-8.53:gain=1:in=0.02:out=0.8

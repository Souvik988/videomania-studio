#!/usr/bin/env bash
# clip10 (10 s): a cappella question, driving song on SECRET, bright song on the generated stage. Run: S=<scripts> P=<project> VOICE=input/vo.wav bash score.sh
set -euo pipefail
PY="${PY:-$HOME/video-production-workbench/OpenMontage/.venv/Scripts/python.exe}"
M=audio/music2
"$PY" "$S/sound_mix.py" "$P" --shots source/shots.js --music-db -22 --voice "$VOICE" \
  --cue $M/glitz_ritz.mp3@0.766:3.45-8.95:gain=0:in=0.02:out=0.12 \
  --cue $M/mozart_nachtmusik.mp3@2.392:8.95-10.16:gain=1:in=0.02:out=0.9

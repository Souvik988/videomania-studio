#!/usr/bin/env bash
# Video Mania workbench bootstrap — repeatable, idempotent, no hidden installs.
# Usage: bash bootstrap.sh [WORKBENCH_DIR]
# Creates/updates: <WORKBENCH>/OpenMontage (pinned), its venv (Python 3.10–3.13),
# faster-whisper/scipy/soundfile/fonttools, HyperFrames CLI cache + core skills, and
# copies the Video Mania OpenMontage extensions in if they are missing.
set -euo pipefail

WB="${1:-$HOME/video-production-workbench}"
OM_REPO="https://github.com/calesthio/OpenMontage"
OM_COMMIT="e45f5b12bd46440b04f3675af9a77d0718e6a254"
HF_VERSION="${VIDEOMANIA_HF_VERSION:-0.8.166}"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1 — install it first ($2)"; exit 2; }; }
need git "https://git-scm.com"
need node "Node >= 22: https://nodejs.org"
need npx "ships with Node"
need ffmpeg "Windows: winget install Gyan.FFmpeg.Essentials | macOS: brew install ffmpeg | Linux: apt install ffmpeg"
need ffprobe "ships with ffmpeg"

node -e 'process.exit(parseInt(process.versions.node)>=22?0:1)' || { echo "Node >= 22 required"; exit 2; }

# Python 3.10-3.13 (3.14 lacks some ML wheels)
PYBIN=""
for c in python3.11 python3.12 python3.13 python3.10 "py -3.11" "py -3.12" "py -3.13" python3 python; do
  if $c -c 'import sys; sys.exit(0 if (3,10)<=sys.version_info[:2]<=(3,13) else 1)' 2>/dev/null; then PYBIN="$c"; break; fi
done
[ -n "$PYBIN" ] || { echo "Need Python 3.10-3.13 on PATH"; exit 2; }
echo "==> Python: $($PYBIN --version)"

mkdir -p "$WB"
FRESH=0
if [ ! -d "$WB/OpenMontage/.git" ]; then
  git clone "$OM_REPO" "$WB/OpenMontage"
  FRESH=1
fi
git -C "$WB/OpenMontage" fetch --quiet origin "$OM_COMMIT" 2>/dev/null || true
if ! git -C "$WB/OpenMontage" diff --quiet; then
  echo "==> OpenMontage has local changes (expected: Video Mania extensions) — not resetting."
else
  git -C "$WB/OpenMontage" checkout --quiet "$OM_COMMIT" 2>/dev/null || echo "   (pinned commit not reachable in a shallow clone; staying on current HEAD)"
fi

VENV="$WB/OpenMontage/.venv"
[ -d "$VENV" ] || $PYBIN -m venv "$VENV"
VPY="$VENV/bin/python"; [ -x "$VPY" ] || VPY="$VENV/Scripts/python.exe"
"$VPY" -m pip install -q --upgrade pip
"$VPY" -m pip install -q -r "$WB/OpenMontage/requirements-dev.txt" faster-whisper scipy soundfile fonttools brotli

# Video Mania OpenMontage extensions (copied from the skill's bundle if absent)
EXT="$SKILL_DIR/openmontage-extensions"
if [ -d "$EXT" ]; then
  if [ "$FRESH" = "1" ]; then
    # fresh clone: the bundle's versions of modified upstream files (subtitle_gen, hyperframes_compose)
    # must replace the pristine ones
    cp -r "$EXT/." "$WB/OpenMontage/" && echo "==> extensions installed (fresh clone)"
  else
    cp -rn "$EXT/." "$WB/OpenMontage/" && echo "==> extensions ensured (existing files kept)"
  fi
fi

npx --yes "hyperframes@$HF_VERSION" --version >/dev/null && echo "==> HyperFrames $HF_VERSION cached"
npx --yes "hyperframes@$HF_VERSION" skills update >/dev/null 2>&1 && echo "==> HyperFrames core skills installed/updated" || echo "   (skills update failed — run it manually)"

mkdir -p "$WB/.pytest-tmp"
( cd "$WB/OpenMontage" && "$VPY" -m pytest tests/contracts -q -p no:cacheprovider --basetemp="$WB/.pytest-tmp/bootstrap" | tail -3 )
"$VPY" "$SKILL_DIR/scripts/preflight.py" | tail -25
echo "{\"workbench\": \"$WB\"}" > "$SKILL_DIR/config.json"
bash "$SKILL_DIR/scripts/install_skills.sh" >/dev/null 2>&1 && echo "==> skill mirrored into every agent host"
echo "==> Done. Workbench: $WB"

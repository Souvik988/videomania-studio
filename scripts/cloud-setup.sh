#!/usr/bin/env bash
# videomania-studio: environment setup for a Claude Code cloud session (Linux).
#
# Run once per session (or set it as the environment's setup script):
#   bash scripts/cloud-setup.sh            # full setup
#   bash scripts/cloud-setup.sh --smoke    # + render-free smoke test (scaffold, check, 3 snapshots)
#   VIDEOMANIA_SKIP_HERK=1 bash scripts/cloud-setup.sh   # skip the 400 MB herk-edit-kit submodule
#
# What it does (nothing paid, nothing private):
#   1. system packages: ffmpeg, Python venv, fonts and the libraries headless Chrome needs; Node >= 22
#   2. reference repos: git submodules under research/ (pinned commits)
#   3. workbench: ~/video-production-workbench with OpenMontage (pinned, Video Mania extensions),
#      its venv and HyperFrames, via the skill's own bootstrap.sh; research/ is linked in
#   4. projects/ in this repo becomes OpenMontage's projects dir, so finished films can be pushed
#   5. HyperFrames' bundled Chrome + doctor
# Google Flow is NOT set up here: it drives a signed-in Chrome on the user's own computer.
# In the cloud the skill runs in prompt-sheet mode (writes clip prompts, waits for the clips).
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WB="${VIDEOMANIA_WORKBENCH:-$HOME/video-production-workbench}"
HF_VERSION="${VIDEOMANIA_HF_VERSION:-0.8.162}"
SKILL="$REPO/.claude/skills/videomania"
SMOKE=0; [ "${1:-}" = "--smoke" ] && SMOKE=1
log() { echo "==> $*"; }
SUDO=""; if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi

# ---------- 1. system packages ----------
if command -v apt-get >/dev/null 2>&1; then
  log "apt packages"
  $SUDO apt-get update -qq || true
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    ffmpeg git ca-certificates curl python3 python3-venv python3-pip fonts-liberation fonts-noto-core \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 >/dev/null
  # Ubuntu 24.04 renamed libasound2
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libasound2t64 >/dev/null 2>&1 || \
    $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq libasound2 >/dev/null 2>&1 || true
fi
need_node=1
if command -v node >/dev/null 2>&1 && node -e 'process.exit(parseInt(process.versions.node)>=22?0:1)'; then need_node=0; fi
if [ "$need_node" = "1" ]; then
  log "Node 22 (NodeSource)"
  curl -fsSL https://deb.nodesource.com/setup_22.x | $SUDO -E bash - >/dev/null
  $SUDO apt-get install -y -qq nodejs >/dev/null
fi
log "node $(node --version), ffmpeg $(ffmpeg -version | head -1 | cut -d' ' -f3), python $(python3 --version | cut -d' ' -f2)"

# ---------- 2. reference repos ----------
log "reference repos (submodules, pinned)"
if [ "${VIDEOMANIA_SKIP_HERK:-0}" = "1" ]; then
  git -C "$REPO" submodule update --init --depth 1 research/awesome-opus5-5-videos research/motion-graphics-skills
else
  git -C "$REPO" submodule update --init --depth 1
fi

# ---------- 3. workbench ----------
mkdir -p "$WB"
if [ ! -e "$WB/research" ]; then ln -s "$REPO/research" "$WB/research"; fi
export VIDEOMANIA_HF_VERSION="$HF_VERSION" HYPERFRAMES_DOCTOR_TIMEOUT_S=180
log "workbench via the skill's bootstrap.sh (OpenMontage pinned, venv, HyperFrames $HF_VERSION)"
bash "$SKILL/scripts/bootstrap.sh" "$WB"

# ---------- 4. projects live in this repo ----------
mkdir -p "$REPO/projects"
cat > "$SKILL/config.json" <<EOF
{"workbench": "$WB", "projects_dir": "$REPO/projects"}
EOF
grep -q OPENMONTAGE_PROJECTS_DIR "$HOME/.bashrc" 2>/dev/null || {
  echo "export VIDEOMANIA_WORKBENCH=\"$WB\"" >> "$HOME/.bashrc"
  echo "export OPENMONTAGE_PROJECTS_DIR=\"$REPO/projects\"" >> "$HOME/.bashrc"
  echo "export VIDEOMANIA_HF_VERSION=\"$HF_VERSION\"" >> "$HOME/.bashrc"
}
log "projects dir: $REPO/projects"

# ---------- 5. HyperFrames Chrome ----------
log "HyperFrames browser"
npx --yes "hyperframes@$HF_VERSION" browser ensure
npx --yes "hyperframes@$HF_VERSION" doctor --json > "$WB/hyperframes-doctor.json" || true
node -e 'const d=require(process.argv[1]); console.log("    doctor ok:", d.ok); if(!d.ok){for(const c of (d.checks||[])) if(c.status!=="ok") console.log("    -", c.name, c.status, c.message||"")}' "$WB/hyperframes-doctor.json" || true
node "$SKILL/assets/motion-kit/motion-kit.test.cjs" | tail -1

# ---------- optional smoke test ----------
if [ "$SMOKE" = "1" ]; then
  log "smoke test: look-book scaffold, check, snapshots"
  VPY="$WB/OpenMontage/.venv/bin/python"
  "$VPY" "$SKILL/scripts/new_composition.py" --project mk-gallery --look warm-editorial --format 9:16 --duration 34 \
    --scenes-js assets/motion-kit/gallery.scenes.js --gallery --force
  ( cd "$REPO/projects/mk-gallery/source" && npx --yes "hyperframes@$HF_VERSION" check | tail -3 )
  ( cd "$REPO/projects/mk-gallery" && npx --yes "hyperframes@$HF_VERSION" snapshot source --describe false --no-end -o snap --at 2.4,9.0,21.8 | tail -2 )
fi
log "ready. Use: /videomania projects/<id>/input/<voiceover> --format 9:16"

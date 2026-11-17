#!/usr/bin/env bash
# OpsGen dev loop. The repo copy (this folder) is the source of truth; builds run in a mirror outside OneDrive
# (node_modules has tens of thousands of files: never let OneDrive sync them).
#
#   bash opsgen-dev.sh sync        mirror source -> $OPSGEN_BUILD (default ~/video-production-workbench/opsgen)
#   bash opsgen-dev.sh install     sync + pnpm install (pinned pnpm through corepack)
#   bash opsgen-dev.sh studio [dir]   sync + start OpsGen Studio (web) on a film folder
#   bash opsgen-dev.sh desktop     sync + start OpsGen Desktop (Studio + the Claude Code chat)
#   bash opsgen-dev.sh test        sync + the package tests
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="${OPSGEN_BUILD:-$HOME/video-production-workbench/opsgen}"
cmd="${1:-sync}"; shift || true

sync() {
  mkdir -p "$DST"
  if command -v robocopy >/dev/null 2>&1; then
    # /MIR mirrors, /XD skips folders that belong to the build tree only
    MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*" robocopy "$(cygpath -w "$SRC")" "$(cygpath -w "$DST")" /MIR /NFL /NDL /NJH /NJS /NP \
      /XD node_modules .film dist out .turbo /XF opsgen-dev.sh >/dev/null || [ $? -lt 8 ]
  else
    rsync -a --delete --exclude node_modules --exclude .film --exclude dist --exclude out "$SRC/" "$DST/"
  fi
  echo "synced -> $DST"
}

case "$cmd" in
  sync) sync ;;
  install) sync; cd "$DST" && corepack pnpm install ;;
  studio) sync; cd "$DST/packages/openfilm" && node bin/opsgen.mjs open "${1:-.}" ;;
  desktop) sync; cd "$DST" && corepack pnpm --filter @opsgen/desktop start ;;
  test) sync; cd "$DST" && corepack pnpm --filter opsgen test ;;
  *) echo "usage: opsgen-dev.sh sync|install|studio [dir]|desktop|test"; exit 2 ;;
esac

#!/usr/bin/env bash
# Video Mania installer — one source of truth, every agent host on this machine.
#
#   bash install_skills.sh            mirror the source skill into each host
#   bash install_skills.sh --check    report drift, write nothing (exit 1 if drift)
#   bash install_skills.sh --target D install into D as well (repeatable)
#
# The source of truth is the skill folder containing this script (the project you edit it in).
# Hosts are only touched when their skills directory already exists, so a machine without
# Claude Code or Qoder is left alone. config.json and caches are never copied.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK=0
EXTRA=()
while [ $# -gt 0 ]; do
  case "$1" in
    --check) CHECK=1 ;;
    --target) EXTRA+=("$2"); shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
  shift
done

HOST_DIRS=()
for host in "$HOME/.claude/skills" "$HOME/.qoder/skills"; do
  [ -d "$host" ] && HOST_DIRS+=("$host/videomania")
done
for t in ${EXTRA+"${EXTRA[@]}"}; do HOST_DIRS+=("$t"); done

if [ ${#HOST_DIRS[@]} -eq 0 ]; then
  echo "No agent host skills directory found under \$HOME (.claude/skills or .qoder/skills)."
  echo "Install Claude Code or Qoder first, or pass --target DIR."
  exit 2
fi

SRC_FILES=$(cd "$SRC" && find . -type f -not -path '*/__pycache__/*' -not -name '*.pyc' \
  -not -name 'config.json' -not -path './.git/*' | sed 's|^\./||' | sort)

drift=0
for DST in "${HOST_DIRS[@]}"; do
  if [ "$(cd "$DST" 2>/dev/null && pwd)" = "$SRC" ]; then
    echo "==> skipping $DST (that is the source itself)"
    continue
  fi
  changed=0
  while IFS= read -r rel; do
    [ -z "$rel" ] && continue
    if [ ! -f "$DST/$rel" ] || ! cmp -s "$SRC/$rel" "$DST/$rel"; then
      echo "    [host] $DST :: $rel"
      changed=$((changed + 1))
      if [ $CHECK -eq 0 ]; then
        mkdir -p "$DST/$(dirname "$rel")"
        cp "$SRC/$rel" "$DST/$rel"
      fi
    fi
  done <<< "$SRC_FILES"

  if [ -d "$DST" ]; then
    while IFS= read -r rel; do
      [ -z "$rel" ] && continue
      case "$rel" in
        __pycache__*|*config.json) continue ;;
      esac
      if [ ! -f "$SRC/$rel" ]; then
        echo "    [stale] $DST :: $rel"
        changed=$((changed + 1))
        [ $CHECK -eq 0 ] && rm -f "$DST/$rel"
      fi
    done < <(cd "$DST" && find . -type f -not -path '*/__pycache__/*' -not -name '*.pyc' | sed 's|^\./||' | sort)
  fi

  if [ $changed -eq 0 ]; then
    echo "==> $DST — in sync"
  else
    drift=1
    echo "==> $DST — $changed file(s) $([ $CHECK -eq 1 ] && echo need syncing || echo synced)"
  fi
done

if [ $CHECK -eq 1 ] && [ $drift -eq 1 ]; then
  echo "DRIFT: run bash install_skills.sh to sync."
  exit 1
fi
echo "Done. Source: $SRC"

#!/usr/bin/env bash
# Build Aseprite from its official source for personal use (Windows, Git Bash).
#
# Aseprite's licence lets you compile it yourself for your own use; it does not let you share the
# binary. So the build stays under <workbench>/tools/ and is never committed or uploaded.
#
# Needs: Visual Studio Build Tools 2022 with the C++ workload, git, Python (for cmake and ninja wheels).
# Usage: bash build_aseprite.sh            (clone if missing, fetch Skia, configure, build)
#        bash build_aseprite.sh --check    (only report whether a built aseprite.exe exists)
set -euo pipefail

WB="${VIDEOMANIA_WORKBENCH:-$HOME/video-production-workbench}"
TOOLS="$WB/tools"; SRC="$TOOLS/aseprite"; SKIA="$TOOLS/skia"; OUT="$SRC/build"
EXE="$OUT/bin/aseprite.exe"

if [ "${1:-}" = "--check" ]; then
  if [ -x "$EXE" ]; then echo "aseprite: $EXE"; "$EXE" --version; exit 0; else echo "aseprite: not built"; exit 1; fi
fi

mkdir -p "$TOOLS"
[ -d "$SRC/.git" ] || git clone --recursive --depth 1 https://github.com/aseprite/aseprite.git "$SRC"

# Skia: the prebuilt package Aseprite pins in laf/misc/skia-tag.txt
TAG="$(tr -d '\r\n' < "$SRC/laf/misc/skia-tag.txt")"
if [ ! -d "$SKIA/out/Release-x64" ]; then
  echo "Fetching Skia $TAG"
  mkdir -p "$SKIA"
  curl -fL -o "$TOOLS/skia.zip" "https://github.com/aseprite/skia/releases/download/$TAG/Skia-Windows-Release-x64.zip"
  unzip -q -o "$TOOLS/skia.zip" -d "$SKIA"
fi

python -m pip install -q --user cmake ninja
PYS="$(python -c "import sysconfig,site,os;print(os.path.join(site.getuserbase(), 'Python'+sysconfig.get_config_var('py_version_nodot'), 'Scripts'))")"

VCVARS="$(ls "/c/Program Files (x86)/Microsoft Visual Studio/2022/"*/VC/Auxiliary/Build/vcvars64.bat "/c/Program Files/Microsoft Visual Studio/2022/"*/VC/Auxiliary/Build/vcvars64.bat 2>/dev/null | head -1 || true)"
[ -n "$VCVARS" ] || { echo "vcvars64.bat not found: install the 'Desktop development with C++' workload in Visual Studio Build Tools 2022"; exit 2; }

w() { cygpath -w "$1"; }
BAT="$TOOLS/build_aseprite.bat"
cat > "$BAT" <<EOF
@echo off
call "$(w "$VCVARS")" >nul
set PATH=$(w "$PYS");%PATH%
cmake -S "$(w "$SRC")" -B "$(w "$OUT")" -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DLAF_BACKEND=skia -DSKIA_DIR="$(w "$SKIA")" -DSKIA_LIBRARY_DIR="$(w "$SKIA/out/Release-x64")" -DSKIA_LIBRARY="$(w "$SKIA/out/Release-x64/skia.lib")" -DENABLE_UPDATER=OFF -DENABLE_NEWS=OFF || exit /b 1
ninja -C "$(w "$OUT")" -j 4 aseprite || exit /b 1
EOF
cmd.exe //c "$(w "$BAT")"
[ -x "$EXE" ] && { echo "Built: $EXE"; "$EXE" --version; } || { echo "Build did not produce aseprite.exe"; exit 3; }

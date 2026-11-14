#!/usr/bin/env bash
# ChatGPT image bridge WITH reference images (likeness, style, character consistency).
#
#   gpt_image_ref.sh "<prompt>" <out.png> --ref photo.png [--ref hero.png ...] [--size 1024x1536]
#
# Same route as ~/.claude/skills/gpt-image-bridge (codex CLI + ChatGPT subscription, no API key), but the
# reference images are attached to the codex prompt with `codex exec -i`. Use it for:
#   - a mascot from the user's photo (likeness): --ref the photo
#   - pose sheets that keep the same character: --ref the approved hero design (and the photo)
#   - plates that match an approved style frame: --ref the style frame
# Calls take 4-6 min; run in the background. Only send a person's photo when they gave it for this purpose.
set -euo pipefail
[[ $# -lt 2 ]] && { echo 'usage: gpt_image_ref.sh "<prompt>" <out.png> --ref img [--ref img] [--size WxH]' >&2; exit 2; }
prompt="$1"; out="$2"; shift 2
size=""; refs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --size) size="$2"; shift 2 ;;
    --ref) refs+=("$1" "$2"); shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
out_dir="$(cd "$(dirname "$out")" && pwd)"; out="$out_dir/$(basename "$out")"
workdir="$(mktemp -d "${TMPDIR:-/tmp}/gpt-image-ref.XXXXXX")"; log="${workdir}.log"
cw="$workdir"; command -v cygpath >/dev/null 2>&1 && cw="$(cygpath -m "$workdir")"
# copy refs into the workdir as PNG (codex reads png/jpg reliably; webp is converted)
args=(); i=0
for ((k = 1; k < ${#refs[@]}; k += 2)); do
  src="${refs[$k]}"; dst="$workdir/ref_$i.png"; i=$((i + 1))
  ffmpeg -v error -y -i "$src" "$dst"
  p="$dst"; command -v cygpath >/dev/null 2>&1 && p="$(cygpath -m "$dst")"
  args+=(-i "$p")
done
size_line=""; [[ -n "$size" ]] && size_line="
SIZE: ${size}"
full="Use your image_generation tool to create ONE image. The attached image(s) are references: follow them for likeness, character design and style as the prompt says.

PROMPT: ${prompt}${size_line}

Requirements:
- You MUST call the image_generation tool (pass the attached reference images to it if it accepts them).
- Do NOT write a script or fabricate a PNG any other way.
- Save the result as out.png in your current working directory (relative path out.png).
- Reply with only the file name."
if ! codex exec --skip-git-repo-check -s workspace-write -C "$cw" "${args[@]}" -- "$full" </dev/null >"$log" 2>&1; then
  echo "gpt_image_ref: codex failed; last lines:" >&2; tail -n 30 "$log" >&2; exit 1
fi
f="$workdir/out.png"
[[ -f "$f" ]] || f="$(ls -t "$workdir"/*.png 2>/dev/null | grep -v '/ref_' | head -1 || true)"
[[ -n "$f" && -f "$f" ]] || { echo "gpt_image_ref: no image produced; log: $log" >&2; tail -n 20 "$log" >&2; exit 1; }
cp "$f" "$out"; echo "$out"

"""EDIT mode: non-destructively improve an existing clip.

Usage:
  edit_clip.py --project ID --clip PATH [--grade bright_clean] [--language en]
               [--music-track PATH --music-license "text"] [--mood warm_corporate]

Steps (source clip is never modified; sha256 re-verified at the end):
  1. ingest.py on the clip (its own dialogue is the speech track) -> transcript + captions
  2. make_audio.py: dialogue cleanup + music (user track with licence, else procedural) + ducked master
  3. OpenMontage `color_grade` (profile) -> graded picture
  4. burn phrase-locked captions (libass) into the graded picture
  5. mux_master.py -> renders/edited.mp4, then qa.py --tag edit
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

HERE = Path(__file__).resolve().parent


def step(args: list[str]) -> None:
    r = subprocess.run([str(vm_env.venv_python()), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(args[:2])}\n{(r.stdout + r.stderr)[-1500:]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--clip", required=True)
    ap.add_argument("--grade", default="bright_clean")
    ap.add_argument("--language", default=None)
    ap.add_argument("--music-track", default=None)
    ap.add_argument("--music-license", default=None)
    ap.add_argument("--mood", default="warm_corporate")
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    clip = Path(args.clip).resolve()
    before = vm_env.sha256(clip)

    ing = [str(HERE / "ingest.py"), "--project", args.project, "--audio", str(clip), "--title", args.project]
    if args.language:
        ing += ["--language", args.language]
    step(ing)
    proj = vm_env.project_dir(args.project)
    dur = float(vm_env.ffprobe(clip)["format"]["duration"])
    vm_env.write_json(proj / "artifacts" / "scene_plan.json", {"version": "1.0", "scenes": [
        {"id": "S01", "type": "talking_head", "description": "edited source clip", "start_seconds": 0.0, "end_seconds": round(dur, 3)}]})

    if args.music_track and not args.music_license:
        raise SystemExit("BLOCKED: --music-track needs --music-license (who owns it / what licence permits this use)")
    music = ({"source": "user", "user_track": str(Path(args.music_track).resolve()), "license": args.music_license, "volume": 0.4}
             if args.music_track else
             {"source": "procedural", "mood": args.mood, "seed": 5, "volume": 0.4,
              "sections": [{"start": 0, "end": dur, "role": "build", "energy": 0.5}], "anchors": []})
    vm_env.write_json(proj / "storyboard" / "audio_plan.json", {"tail_seconds": 0.0, "music": music, "sfx": [],
                                                              "mix": {"loudness_target": -14, "music_volume_during_speech": 0.18}})
    step([str(HERE / "make_audio.py"), "--project", args.project])

    from tools.enhancement.color_grade import ColorGrade
    graded = proj / "previews" / "graded.mp4"
    r = ColorGrade().execute({"input_path": str(proj / "input" / clip.name), "output_path": str(graded), "profile": args.grade})
    if not r.success:
        raise SystemExit(f"FAILED: color_grade: {r.error}")

    captioned = proj / "previews" / "captioned.mp4"
    srt = (proj / "transcript" / "captions.srt").as_posix().replace(":", "\\:")
    style = "FontName=Inter,Bold=1,FontSize=13,PrimaryColour=&H00DFE8EC,BackColour=&H99121010,BorderStyle=4,Outline=0,Shadow=0,MarginV=60,Alignment=2"
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(graded), "-vf", f"subtitles='{srt}':force_style='{style}'",
                "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(captioned)])
    out = proj / "renders" / "edited.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    step([str(HERE / "mux_master.py"), "--video", str(captioned), "--mix", str(proj / "audio" / "mix.wav"), "--out", str(out)])

    after = vm_env.sha256(clip)
    w = vm_env.ffprobe(clip)["streams"][0]
    qa = subprocess.run([str(vm_env.venv_python()), str(HERE / "qa.py"), "--project", args.project, "--video", str(out),
                         "--tag", "edit", "--expect", f"{w.get('width')}x{w.get('height')}@30"], capture_output=True, text=True)
    print(json.dumps({"edited": str(out), "source_unchanged": before == after, "source_sha256": before,
                      "output_sha256": vm_env.sha256(out), "qa_exit": qa.returncode,
                      "qa_tail": qa.stdout[-900:]}, indent=2))
    return 0 if before == after else 1


if __name__ == "__main__":
    raise SystemExit(main())

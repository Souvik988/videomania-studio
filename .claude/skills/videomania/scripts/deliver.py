"""Package the delivery folder. Lists only files that actually exist.

Usage: deliver.py --project ID --final PATH [--preview PATH] [--thumb-at 26.5]

Creates projects/<ID>/delivery/:
  final.mp4, preview.mp4 (540 px proxy), thumbnail.png, captions.srt/.vtt,
  audio-stems/{voice,music,sfx,mix}.wav, editable-project/ (HyperFrames source +
  storyboard + artifacts + transcript), asset-provenance.json, quality-report.md,
  MANIFEST.json (sha256 + ffprobe of every delivered media file).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--final", required=True)
    ap.add_argument("--thumb-at", type=float, default=None)
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    proj = vm_env.project_dir(args.project)
    d = proj / "delivery"
    final = Path(args.final)
    if not final.is_file():
        raise SystemExit(f"--final does not exist: {final}")
    # The delivery folder is rebuilt from scratch, so a master that lives inside it
    # would be deleted before it could be copied. Park it outside first.
    if d.exists() and final.resolve().is_relative_to(d.resolve()):
        staged = proj / "renders" / f"staged_{final.name}"
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(final, staged)
        final = staged
    if d.exists():
        shutil.rmtree(d)
    (d / "audio-stems").mkdir(parents=True)
    shutil.copy2(final, d / "final.mp4")
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(final), "-vf", "scale=540:-2", "-c:v", "libx264", "-crf", "28",
                "-preset", "veryfast", "-c:a", "aac", "-b:a", "96k", str(d / "preview.mp4")])
    dur = float(vm_env.ffprobe(final)["format"]["duration"])
    t = args.thumb_at if args.thumb_at is not None else dur * 0.8
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(final), "-frames:v", "1", str(d / "thumbnail.png")])
    for name in ("captions.srt", "captions.vtt"):
        src = proj / "transcript" / name
        if src.exists():
            shutil.copy2(src, d / name)
    for stem, src in {"voice": "audio/stems/voice.wav", "music": "audio/stems/music.wav", "sfx": "audio/stems/sfx.wav", "mix": "audio/mix.wav"}.items():
        if (proj / src).exists():
            shutil.copy2(proj / src, d / "audio-stems" / f"{stem}.wav")
    ep = d / "editable-project"
    ignore = shutil.ignore_patterns(".hyperframes", "*.hf-transaction*", "__pycache__")
    for sub in ("source", "storyboard", "brief", "artifacts", "transcript"):
        if (proj / sub).exists():
            shutil.copytree(proj / sub, ep / sub, ignore=ignore)
    (ep / "README.md").write_text(
        "# Editable project\n\n"
        "- `source/` is a HyperFrames composition (HTML/SVG/GSAP). Preview: `npx hyperframes preview` in `source/`;\n"
        "  render: `npx hyperframes@0.8.162 render -q delivery -o final.mp4`.\n"
        "- Every visual is computed from time in `render(t)` inside `source/index.html`; caption timings live in\n"
        "  `source/data.js` (generated from `transcript/words.json`).\n"
        "- Audio stems are in `../audio-stems/`; the composition plays `source/audio/mix.wav`.\n"
        "- No After Effects (.aep), Premiere or Resolve project is included; none was generated.\n", encoding="utf-8")

    try:  # measured-evidence report; skipped (and said so) if QA has not been run on the final
        import quality_report
        quality_report.build  # noqa: B018
        (d / "quality-report.md").write_text(quality_report.build(proj, "final"), encoding="utf-8")
    except FileNotFoundError as e:
        print(f"WARNING: quality-report.md not produced (missing QA evidence: {e.filename})")

    manifest = vm_env.read_json(proj / "artifacts" / "asset_manifest.json")
    audio_rep = proj / "audio" / "stems" / "music.json"
    prov = {"project": args.project, "assets": manifest["assets"],
            "music_metadata": vm_env.read_json(audio_rep) if audio_rep.exists() else None,
            "total_cost_usd": manifest.get("metadata", {}).get("total_cost_usd", 0.0)}
    vm_env.write_json(d / "asset-provenance.json", prov)

    files = {}
    for p in sorted(d.rglob("*")):
        if p.is_file() and "editable-project" not in p.parts:
            entry = {"bytes": p.stat().st_size, "sha256": vm_env.sha256(p)}
            if p.suffix in (".mp4", ".wav", ".png"):
                pr = vm_env.ffprobe(p)
                entry["streams"] = [f"{s['codec_type']}:{s.get('codec_name')}" + (f" {s.get('width')}x{s.get('height')}" if s.get("width") else "") for s in pr["streams"]]
                if "duration" in pr["format"]:
                    entry["duration_s"] = round(float(pr["format"]["duration"]), 3)
            files[str(p.relative_to(d)).replace("\\", "/")] = entry
    files["editable-project/"] = {"files": sum(1 for p in ep.rglob("*") if p.is_file())}
    vm_env.write_json(d / "MANIFEST.json", files)
    print(json.dumps({"delivery": str(d), "files": list(files)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

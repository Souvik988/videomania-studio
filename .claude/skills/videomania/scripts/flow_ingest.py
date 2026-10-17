"""Ingest a Flow download into a project: safe extract, probe, QC sheet, provenance.

Usage: flow_ingest.py --dir <project>/assets/flow/G1 --id G1 [--project ID]
       flow_ingest.py --dir <project>/assets/flow/G1 --id G1 --file PATH [--expect-aspect 9:16] [--expect-duration 8]
                      (prompt-sheet mode: the user generated the clip in Flow themselves and supplied the file)

Expects <dir>/flow-download.zip (or .mp4/.jpg/.png) written by `flow_once.mjs fetch`.
- Extracts zips safely (no path traversal) into <dir>/extracted/ and picks the media file.
- Probes codec/size/fps/duration, measures the active picture with cropdetect (Flow output can
  contain letterbox bars) and the audio loudness.
- Writes <dir>/qc/contact_sheet.png (8 frames) and full-res frames at 25/50/75 %.
- Writes <dir>/provenance.json joining the click ledger entry for --id (model, prompt, credits,
  approval words). Watermarks are left untouched.
Prints a JSON summary. Visual QC (faces, hands, continuity) is still the agent's job: read the
contact sheet and frames before using the clip.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

MEDIA = {".mp4", ".mov", ".webm", ".jpg", ".jpeg", ".png", ".webp"}


def safe_extract(zpath: Path, dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    root = dest.resolve()
    out = []
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            target = (dest / info.filename).resolve()
            if not str(target).startswith(str(root) + os.sep):
                raise SystemExit(f"REFUSED: unsafe path in zip: {info.filename}")
        z.extractall(dest)
        out = [dest / i.filename for i in z.infolist() if not i.is_dir()]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--id", required=True)
    ap.add_argument("--file", help="a clip the user generated in Flow and supplied (prompt-sheet / cloud mode)")
    ap.add_argument("--expect-aspect", help="e.g. 9:16 - reported as a mismatch if the clip differs")
    ap.add_argument("--expect-duration", type=float, help="seconds requested on the generation sheet")
    args = ap.parse_args()
    d = Path(args.dir).resolve()
    if args.file:
        import shutil
        f = Path(args.file).resolve()
        if not f.exists() or f.suffix.lower() not in MEDIA | {".zip"}:
            print(f"BLOCKED: {f} is missing or not a supported media file")
            return 2
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("flow-download*"):
            old.unlink()
        shutil.copy2(f, d / ("flow-download" + f.suffix.lower()))
    src = next((p for p in d.iterdir() if p.name.startswith("flow-download")), None)
    if not src:
        print(f"BLOCKED: no flow-download.* in {d}")
        return 2
    files = safe_extract(src, d / "extracted") if src.suffix == ".zip" else [src]
    media = [f for f in files if f.suffix.lower() in MEDIA]
    if not media:
        print("BLOCKED: no media file in download")
        return 2
    m = media[0]
    is_video = m.suffix.lower() in {".mp4", ".mov", ".webm"}
    pr = vm_env.ffprobe(m)
    v = next((s for s in pr["streams"] if s["codec_type"] == "video"), {})
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    summary: dict = {
        "file": str(m), "sha256": vm_env.sha256(m),
        "codec": v.get("codec_name"), "width": v.get("width"), "height": v.get("height"),
        "fps": v.get("r_frame_rate"), "duration_s": float(pr["format"].get("duration", 0) or 0),
        "audio": bool(a),
    }
    checks = {}
    if args.expect_aspect and summary["width"] and summary["height"]:
        aw, ah = (float(x) for x in args.expect_aspect.split(":"))
        checks["aspect_ok"] = abs(summary["width"] / summary["height"] - aw / ah) < 0.02
    if args.expect_duration:
        checks["duration_ok"] = abs(summary["duration_s"] - args.expect_duration) <= 0.5
    if checks:
        summary["checks"] = checks
    qc = d / "qc"
    qc.mkdir(exist_ok=True)
    if is_video:
        p = vm_env.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(m), "-vf", "cropdetect=limit=24:round=2:reset=0",
                        "-an", "-f", "null", "-"], check=False)
        crops = re.findall(r"crop=(\d+:\d+:\d+:\d+)", p.stderr)
        summary["active_picture"] = max(set(crops), key=crops.count) if crops else None
        if a:
            summary["loudness"] = vm_env.loudness(m)
        dur = summary["duration_s"]
        times = [dur * k / 9 for k in range(1, 9)]
        for i, t in enumerate(times):
            vm_env.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(m), "-frames:v", "1", "-vf", "scale=270:-2", str(qc / f"s{i}.png")])
        ins = sum([["-i", str(qc / f"s{i}.png")] for i in range(8)], [])
        vm_env.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex",
                    "[0][1][2][3]hstack=4[a];[4][5][6][7]hstack=4[b];[a][b]vstack", str(qc / "contact_sheet.png")])
        for i in range(8):
            (qc / f"s{i}.png").unlink(missing_ok=True)
        for pct in (25, 50, 75):
            vm_env.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{dur * pct / 100:.3f}", "-i", str(m), "-frames:v", "1", str(qc / f"full_{pct}.png")])
    ledger = Path(os.environ.get("FLOW_MCP_DIR", Path.home() / "video-production-workbench" / "mcp" / "google-flow-mcp")) / "outputs" / "flow-click-ledger.jsonl"
    entry = None
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("id") == args.id:
                entry = row
    prov = {
        "id": args.id, "asset": str(m), **{k: summary[k] for k in ("sha256", "width", "height", "fps", "duration_s")},
        "source_tool": ("Google Flow, generated by the user from the generation sheet and supplied as a file (prompt-sheet mode)"
                        if args.file else "google-flow MCP composer setup + one user-approved real click (flow_once.mjs)"),
        "supplied_file": str(Path(args.file).name) if args.file else None,
        "click_ledger": entry,
        "watermark": "Flow's visible mark kept; no removal or crop applied",
        "license": "per Google Flow terms for the signed-in account; AI-generated, label as such",
        "measured": {k: summary.get(k) for k in ("active_picture", "loudness", "audio")},
    }
    vm_env.write_json(d / "provenance.json", prov)
    print(json.dumps({**summary, "qc_dir": str(qc), "provenance": str(d / "provenance.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate delivery/quality-report.md from measured evidence only.

Usage: quality_report.py --project ID [--tag final] [--out PATH]

Every number comes from qa/<tag>/*.json or the critic reports; nothing is
estimated. Critic totals are parsed from `qa/critic_passN.md` ("**Total**" table
row or a "Total: NN" line). A listed artifact is only linked if the file exists.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def critic_total(path: Path) -> int | None:
    """Score from the rubric table's Total row: | Total | <max> | <score> | ... |.

    The row carries the maximum (100) before the score, so the *score* is the
    number after the max. Falls back to a "Total: NN/100" sentence. Returns None
    (reported as 'unparsed') rather than ever guessing.
    """
    t = path.read_text(encoding="utf-8", errors="replace")
    for line in t.splitlines():
        if re.match(r"\s*\|\s*\**Total\**\s*\|", line):
            cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
            nums = [int(c) for c in cells[1:] if re.fullmatch(r"\d{1,3}", c)]
            if len(nums) >= 2 and nums[0] == 100 and 0 <= nums[1] <= 100:
                return nums[1]
            if len(nums) == 1 and 0 <= nums[0] <= 100:
                return nums[0]
    m = re.search(r"[Tt]otal[^\n\d]{0,30}(\d{1,3})\s*/\s*100", t)
    return int(m.group(1)) if m else None


def exists(p: Path) -> str:
    return "present" if p.exists() else "NOT PRODUCED"


def build(proj: Path, tag: str = "final") -> str:
    q = proj / "qa" / tag
    summ = vm_env.read_json(q / "summary.json")
    tech = vm_env.read_json(q / "technical_report.json")
    aud = vm_env.read_json(q / "audio_report.json") if (q / "audio_report.json").exists() else {}
    cap = vm_env.read_json(q / "caption_report.json") if (q / "caption_report.json").exists() else {}
    rel = lambda p: str(p.relative_to(proj)).replace("\\", "/")  # noqa: E731
    L: list[str] = []
    L.append(f"# Quality report — {proj.name}\n")
    L.append("_Generated from measured files. Audio is **measured, not listened to**. Scores are editorial judgements by an "
             "independent critic, not audience data._\n")
    v, a = tech.get("video") or {}, tech.get("audio") or {}
    L.append("## Deliverable")
    L.append(f"- File: `{tech['path']}`  ({tech['size_bytes'] // 1024} KB)")
    L.append(f"- Video: {v.get('codec_name')} {v.get('width')}x{v.get('height')} @ {v.get('avg_frame_rate')} {v.get('pix_fmt')}, "
             f"{tech['duration_s']:.2f} s (plan {tech['planned_end_s']:.2f} s)")
    L.append(f"- Audio: {a.get('codec_name')} {a.get('sample_rate')} Hz, {a.get('channels')} ch\n")
    L.append("## Technical gates (`qa/%s/summary.json`)" % tag)
    L.append("| gate | result | observed |\n|---|---|---|")
    for k, d in summ["details"].items():
        obs = json.dumps(d.get("observed"), ensure_ascii=False)
        L.append(f"| {k} | {'PASS' if d['pass'] else '**FAIL**'} | {obs[:140]} |")
    L.append(f"\n**All technical gates pass: {summ['all_technical_gates_pass']}**\n")
    m = tech.get("motion", {})
    L.append("## Motion\n"
             f"- frames changing visibly: {m.get('changing_frame_ratio')}, median changed pixels/frame: {m.get('median_changed_px')}, "
             f"still runs > 0.6 s: {len(m.get('still_runs_over_0p6s', []))}, end hold: {m.get('end_hold_s')} s\n")
    if aud:
        L.append("## Audio (measured)")
        lm = aud.get("loudness", {})
        L.append(f"- Integrated {lm.get('integrated_lufs')} LUFS, LRA {lm.get('lra_lu')} LU, true peak {lm.get('true_peak_dbtp')} dBTP")
        L.append(f"- A/V offset vs master: {aud.get('av_offset_ms')}")
        L.append(f"- Speech-gap check: {aud.get('speech_gaps')}; speech over bed: {aud.get('speech_over_bed_db')} dB")
        L.append(f"- Stereo: {aud.get('stereo')}")
        ar = proj / "qa" / "audio_report.json"
        if ar.exists():
            r = vm_env.read_json(ar)
            mu = r.get("music", {})
            L.append(f"- Music source: **{mu.get('source')}** — {(mu.get('provenance') or {}).get('source', mu.get('license', ''))}; "
                     f"{mu.get('bpm')} BPM, {mu.get('key')} {mu.get('scale')}; narration-anchor fit error {mu.get('anchor_mean_error_s')} s")
        L.append("")
    if cap:
        L.append("## Captions")
        L.append(f"- {cap.get('cues')} cues; overlaps {cap.get('overlaps')}; >20 cps: {cap.get('cps_over_20')}; "
                 f"glyph coverage missing: {(cap.get('glyph_coverage') or {}).get('missing')}\n")
    seek = proj / "qa" / "seek_test_final" / "seek_report.json"
    if seek.exists():
        s = vm_env.read_json(seek)
        L.append(f"## Determinism\n- Shuffled-order seek test: {sum(r['identical'] for r in s['frames'])}/{len(s['frames'])} frames pixel-identical "
                 f"(`{rel(seek)}`)\n")
    L.append("## Independent critic passes")
    totals = []
    for p in sorted((proj / "qa").glob("critic_pass*.md")):
        t = critic_total(p)
        totals.append(t)
        L.append(f"- `{rel(p)}`: total **{t if t is not None else 'unparsed'}**/100")
    if not totals:
        L.append("- none recorded")
    log = proj / "qa" / "review_log.md"
    if log.exists():
        L.append(f"\nReview/repair log: `{rel(log)}`")
    L.append("\n## Evidence files")
    for name in ("contact_sheet.png", "phone_preview.png", "strips"):
        L.append(f"- `qa/{tag}/{name}`: {exists(q / name)}")
    L.append("\n## Not included")
    L.append("- No native After Effects (.aep), Premiere or Resolve project; no 4K master; no LUT; no 1:1 / 16:9 re-layout unless listed above.")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--tag", default="final")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    proj = vm_env.project_dir(args.project)
    out = Path(args.out) if args.out else proj / "delivery" / "quality-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(proj, args.tag), encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

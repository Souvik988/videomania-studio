"""Tighten raw talking recordings: cut dead air between phrases, propose mistake cuts, render once.

Usage:
  cut_speech.py --project ID [--words transcript/words.json] [--media PATH]
                [--gap 0.25] [--beat 0.30] [--tight 0.12] [--approved cuts.json] [--render]

Steps:
  1. phrases     words separated by less than --gap seconds belong to one phrase (one breath)
  2. silences    the pause between two phrases is shortened, never removed: --beat seconds after a
                 comma, colon or list marker ("First,"), --tight seconds elsewhere. Nothing inside a
                 phrase is ever cut, and the voice is never sped up.
  3. mistakes    retakes (a phrase restarted with the same opening words) and stand-alone fillers
                 (um, uh, hmm, matlab-as-filler only when silent on both sides) are written to
                 edit/cut_candidates.json for the USER to review. They are applied only from an
                 approved file (--approved), keeping the LAST clean take.
  4. EDL         edit/edl.json (keep segments in source time, frame-snapped) and
                 edit/words.retimed.json (every kept word mapped to output time) for captions.
  5. render      with --render: ONE ffmpeg pass (trim/atrim + concat, 10 ms audio fades at joins)
                 to edit/cut.<ext>, so picture and sound cannot drift at the joins.

Rules from herk-edit-kit's editing playbook (MIT, github.com/nateherkai/herk-edit-kit):
  cut between phrases, never inside one; keep natural beats after commas and list markers; a
  filler that runs straight into the next word stays; words end 40-80 ms before the consonant
  dies, so 80 ms is kept after each phrase; encoding segments separately and concatenating drifts
  lip sync, so select exact frames in one pass.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

FILLERS = {"um", "uh", "umm", "uhh", "hmm", "erm", "ah", "eh", "matlab", "basically"}
BEAT_END = (",", ":", ";", "—", "–")
HEAD_PAD, TAIL_PAD = 0.04, 0.08


def clean(w: str) -> str:
    return re.sub(r"[^\w']", "", w.lower())


def phrases_of(words: list[dict], gap: float) -> list[list[dict]]:
    out, cur = [], []
    for w in words:
        if cur and w["start"] - cur[-1]["end"] >= gap:
            out.append(cur)
            cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    return out


def candidates(phr: list[list[dict]]) -> list[dict]:
    """Retakes and stand-alone fillers, for the user to approve."""
    cands = []
    for i, p in enumerate(phr):
        toks = [clean(w["word"]) for w in p]
        if toks and all(t in FILLERS for t in toks):
            cands.append({"id": f"F{i}", "kind": "filler", "phrase": i, "text": " ".join(w["word"] for w in p),
                          "start": p[0]["start"], "end": p[-1]["end"], "default": "cut"})
            continue
        if i + 1 < len(phr):
            nxt = [clean(w["word"]) for w in phr[i + 1]]
            k = 0
            while k < min(len(toks), len(nxt)) and toks[k] == nxt[k]:
                k += 1
            if k >= 2 or (k >= 1 and len(toks) <= 2):
                cands.append({"id": f"R{i}", "kind": "retake", "phrase": i,
                              "text": " ".join(w["word"] for w in p),
                              "next_take": " ".join(w["word"] for w in phr[i + 1]),
                              "start": p[0]["start"], "end": p[-1]["end"], "default": "cut",
                              "why": f"next phrase restarts with the same {k} word(s); keep the last clean take"})
    return cands


def build_edl(phr: list[list[dict]], cut_phrases: set[int], beat: float, tight: float, fps: float,
              duration: float) -> list[dict]:
    snap = lambda t: round(round(t * fps) / fps, 4)  # noqa: E731
    kept = [p for i, p in enumerate(phr) if i not in cut_phrases]
    segs = []
    for j, p in enumerate(kept):
        start = max(0.0, p[0]["start"] - HEAD_PAD)
        end = min(duration, p[-1]["end"] + TAIL_PAD)
        if j + 1 < len(kept):
            gap = kept[j + 1][0]["start"] - p[-1]["end"]
            hold = beat if p[-1]["word"].strip().endswith(BEAT_END) else tight
            end = min(duration, p[-1]["end"] + max(TAIL_PAD, min(gap - HEAD_PAD, hold)))
        segs.append({"src_start": snap(start), "src_end": snap(end), "words": len(p),
                     "text": " ".join(w["word"] for w in p)[:80]})
    merged = []
    for s in segs:  # merge segments that touch (gap kept whole)
        if merged and s["src_start"] <= merged[-1]["src_end"] + 1e-3:
            merged[-1]["src_end"] = max(merged[-1]["src_end"], s["src_end"])
            merged[-1]["words"] += s["words"]
        else:
            merged.append(dict(s))
    t = 0.0
    for s in merged:
        s["out_start"] = round(t, 4)
        t += s["src_end"] - s["src_start"]
        s["out_end"] = round(t, 4)
    return merged


def retime(words: list[dict], edl: list[dict]) -> list[dict]:
    out = []
    for w in words:
        for s in edl:
            if s["src_start"] - 1e-3 <= w["start"] and w["end"] <= s["src_end"] + 0.1:
                off = s["out_start"] - s["src_start"]
                out.append({**w, "start": round(w["start"] + off, 3), "end": round(min(w["end"], s["src_end"]) + off, 3)})
                break
    return out


def render(media: Path, edl: list[dict], dest: Path, has_video: bool) -> None:
    parts, labels = [], []
    for i, s in enumerate(edl):
        a, b = s["src_start"], s["src_end"]
        fade = min(0.01, (b - a) / 4)
        if has_video:
            parts.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fade},afade=t=out:st={max(0.0, b - a - fade):.4f}:d={fade}[a{i}]")
        labels.append((f"[v{i}]" if has_video else "") + f"[a{i}]")
    n = len(edl)
    parts.append("".join(labels) + f"concat=n={n}:v={1 if has_video else 0}:a=1" + ("[v][a]" if has_video else "[a]"))
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(media), "-filter_complex", ";".join(parts)]
    if has_video:
        cmd += ["-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart"]
    else:
        cmd += ["-map", "[a]", "-c:a", "pcm_s24le"]
    cmd.append(str(dest))
    vm_env.run(cmd)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--words", default="transcript/words.json")
    ap.add_argument("--media", help="source recording (default: input/SOURCE.json copy)")
    ap.add_argument("--gap", type=float, default=0.25, help="pause that separates two phrases")
    ap.add_argument("--beat", type=float, default=0.30, help="pause kept after a comma or list marker")
    ap.add_argument("--tight", type=float, default=0.12, help="pause kept between other phrases")
    ap.add_argument("--approved", help="JSON list of approved candidate ids, or the candidates file with decisions")
    ap.add_argument("--render", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    vm_env.ensure_openmontage_on_path()
    proj = vm_env.project_dir(a.project)
    data = vm_env.read_json(proj / a.words)
    words = data["words"] if isinstance(data, dict) else data
    media = Path(a.media) if a.media else Path(vm_env.read_json(proj / "input" / "SOURCE.json")["copy"])
    pr = vm_env.ffprobe(media)
    duration = float(pr["format"]["duration"])
    vstream = next((s for s in pr["streams"] if s["codec_type"] == "video"), None)
    fps = eval(vstream["avg_frame_rate"]) if vstream else 100.0  # noqa: S307 - ffprobe rational
    phr = phrases_of(words, a.gap)
    out_dir = proj / "edit"
    out_dir.mkdir(exist_ok=True)
    cands = candidates(phr)
    vm_env.write_json(out_dir / "cut_candidates.json", {"note": "Review with the user. Approve by listing ids in "
                                                        "an approved file; nothing here is applied automatically.",
                                                        "candidates": cands})
    cut = set()
    if a.approved:
        ap_data = vm_env.read_json(Path(a.approved))
        ids = set(ap_data if isinstance(ap_data, list) else [c["id"] for c in ap_data.get("candidates", []) if c.get("decision") == "cut"])
        cut = {c["phrase"] for c in cands if c["id"] in ids}
    edl = build_edl(phr, cut, a.beat, a.tight, fps, duration)
    vm_env.write_json(out_dir / "edl.json", {"source": str(media), "fps": fps, "segments": edl, "cut_phrases": sorted(cut)})
    vm_env.write_json(out_dir / "words.retimed.json", {"words": retime(words, edl)})
    new_dur = edl[-1]["out_end"] if edl else 0.0
    report = {"phrases": len(phr), "segments": len(edl), "source_s": round(duration, 2), "output_s": round(new_dur, 2),
              "removed_s": round(duration - new_dur, 2), "mistake_candidates": len(cands), "applied_cuts": sorted(cut)}
    if a.render:
        dest = out_dir / ("cut.mp4" if vstream else "cut.wav")
        render(media, edl, dest, bool(vstream))
        report["rendered"] = str(dest)
        report["rendered_duration_s"] = round(float(vm_env.ffprobe(dest)["format"]["duration"]), 3)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

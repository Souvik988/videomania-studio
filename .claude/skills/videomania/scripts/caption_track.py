"""Build the burned-in caption data for a HyperFrames composition.

Usage: caption_track.py --project ID [--mode phrase|chunk] [--friction w1,w2] [--go w1,w2]
                        [--fps 30] [--out source/data.js]

Reads transcript/captions.json (phrase-locked cues from ingest.py) and writes
window.CUES = [{s, e, lines: [[{w, s, e, c}, ...], ...], c?}] where `e` is the
display end (never past the next cue's start, so cues cannot double-expose)
and `c` is an accent class that the composition applies ONLY once the word
has been spoken.

Modes (see references/storytelling-and-retention.md §7):
  phrase  two-line phrase-locked cues with word-by-word brightening (16:9, explainers)
  chunk   1-3 words per cue, split on phrase boundaries, hard swap, shown 2 frames before the
          first word; the accent class is applied to the WHOLE chunk (cue-level "c") so colour
          lands on 25-45 % of chunks with meaning (9:16 short-form house style, herk-edit-kit)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def _key(word: str) -> str:
    """Accent lookup key: case-insensitive, ignoring surrounding punctuation ("orders," == "Orders")."""
    return word.strip().strip(".,?!;:—–-\"'“” ").lower()


BREAK = (",", ".", "?", "!", ";", ":", "—", "–")


def chunk_cues(cues: list[dict], fr: set[str], go: set[str], fps: float, max_words: int = 3,
               max_chars: int = 18) -> list[dict]:
    words = [w for c in cues for w in c["words"]]
    chunks: list[list[dict]] = []
    cur: list[dict] = []
    for i, w in enumerate(words):
        cur.append(w)
        text = " ".join(x["word"].strip() for x in cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        at_break = w["word"].strip().endswith(BREAK)
        gap = nxt is not None and nxt["start"] - w["end"] > 0.25
        too_long = nxt is not None and len(text) + 1 + len(nxt["word"].strip()) > max_chars
        if at_break or gap or len(cur) >= max_words or too_long or nxt is None:
            chunks.append(cur)
            cur = []
    lead = 2.0 / fps
    out = []
    for i, ch in enumerate(chunks):
        s = max(0.0, ch[0]["start"] - lead)
        nxt_s = max(0.0, chunks[i + 1][0]["start"] - lead) if i + 1 < len(chunks) else None
        e = ch[-1]["end"] + 0.35 if nxt_s is None else min(ch[-1]["end"] + 0.6, nxt_s - 1.0 / fps)
        keys = {_key(w["word"]) for w in ch}
        cls = "fr" if keys & fr else ("go" if keys & go else "")
        e = max(e, s + 0.1) if nxt_s is None else min(max(e, s + 0.1), nxt_s - 1.0 / fps)
        out.append({"s": round(s, 3), "e": round(e, 3), "c": cls,
                    "lines": [[{"w": w["word"].strip(), "s": w["start"], "e": w["end"], "c": cls} for w in ch]]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--friction", default="")
    ap.add_argument("--go", default="")
    ap.add_argument("--out", default="source/data.js")
    ap.add_argument("--mode", choices=["phrase", "chunk"], default="phrase")
    ap.add_argument("--fps", type=float, default=30.0)
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    proj = vm_env.project_dir(args.project)
    cues = vm_env.read_json(proj / "transcript" / "captions.json")
    fr = {_key(w) for w in args.friction.split(",") if w.strip()}
    go = {_key(w) for w in args.go.split(",") if w.strip()}
    out = []
    for i, c in enumerate(cues if args.mode == "phrase" else []):
        words = list(c["words"])
        lines, k = [], 0
        for line in c["lines"]:
            # a timed word may hold several spaced pieces ("pata hai"), so
            # consume words until their pieces cover this line's pieces
            n, j = len(line.split()), k
            while j < len(words) and n > 0:
                n -= len(words[j]["word"].split())
                j += 1
            lines.append([{"w": w["word"].strip(), "s": w["start"], "e": w["end"],
                           "c": "fr" if _key(w["word"]) in fr else ("go" if _key(w["word"]) in go else "")}
                          for w in words[k:j]])
            k = j
        assert k == len(words), f"cue {i}: line split does not match words"
        nxt = cues[i + 1]["start"] if i + 1 < len(cues) else None
        e = c["display_end"] if nxt is None else min(c["display_end"], nxt - 0.04)
        out.append({"s": c["start"], "e": round(e, 3), "lines": lines})
    if args.mode == "chunk":
        out = chunk_cues(cues, fr, go, args.fps)
        accented = sum(1 for c in out if c["c"]) / max(1, len(out))
        print(f"chunk mode: {len(out)} chunks, {accented:.0%} accented (house range 25-45 %)", file=sys.stderr)
    for a, b in zip(out, out[1:]):
        assert a["e"] <= b["s"] - 0.03, "overlapping caption windows"
    path = proj / args.out
    path.write_text("// Generated by caption_track.py from transcript/captions.json — do not hand-edit timings\n"
                    "window.CUES = " + json.dumps(out, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(json.dumps({"cues": len(out), "out": str(path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

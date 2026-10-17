"""Voiceover ingest: inspect, preserve, transcribe, align, caption.

Usage:
  ingest.py --project ID --audio PATH [--title T] [--language en|hi|bn|...]
            [--model small] [--pipeline voiceover-film]

Steps (all evidence written under projects/<ID>/):
  1. ffprobe + loudness + silence + clipping report  -> qa/audio_input_report.json
  2. immutable copy + sha256                         -> input/<name>, input/SOURCE.json
  3. OpenMontage `transcriber` (faster-whisper, word timestamps) -> transcript/transcript.json
  4. word list, low-confidence review list, phrases split on pauses -> transcript/words.json, phrases.json
  5. OpenMontage `subtitle_gen` SRT + VTT            -> transcript/captions.srt/.vtt

The original recording is never modified; cleanup happens later on a copy.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

LOW_CONF = 0.55          # word probability below this goes on the review list
PHRASE_GAP_S = 0.28      # pause that splits a phrase
SENTENCE_GAP_S = 0.45    # pause that strongly suggests a beat boundary


def silence_map(path: Path, noise_db: float = -38, min_d: float = 0.25) -> list[dict]:
    p = vm_env.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                    f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"])
    out, cur = [], {}
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            cur = {"start": float(m.group(1))}
        m = re.search(r"silence_end: ([\d.]+) \| silence_duration: ([\d.]+)", line)
        if m and cur:
            cur.update(end=float(m.group(1)), duration=float(m.group(2)))
            out.append(cur)
            cur = {}
    return out


def clipping_ratio(path: Path) -> float:
    import numpy as np
    import soundfile as sf
    tmp = path.with_suffix(".probe.wav")
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "16000", str(tmp)])
    x, _ = sf.read(str(tmp))
    tmp.unlink(missing_ok=True)
    return float((np.abs(x) > 0.995).mean())



MAX_LINE = 34          # characters per caption line
MIN_CUE_S = 0.8        # cues shorter than this merge into a neighbour (as their own line)
LINGER_S = 0.6         # a cue stays up to this long after its last word (reading time)


def _balance(text: str) -> list[str]:
    """Split into <= 2 lines; prefer a sentence boundary, else the most balanced space."""
    if len(text) <= MAX_LINE:
        return [text]
    m = re.search(r"[.!?] ", text)
    if m and max(m.end() - 1, len(text) - m.end()) <= MAX_LINE + 4:
        return [text[: m.end() - 1], text[m.end():]]
    spaces = [i for i, ch in enumerate(text) if ch == " "]
    best = min(spaces, key=lambda i: abs(len(text) / 2 - i))
    return [text[:best], text[best + 1:]]


def _split_long(ph: list[dict]) -> list[list[dict]]:
    """Split a phrase until each piece fits two caption lines.

    Prefer a break after a comma/dash/semicolon nearest the middle; otherwise the most balanced
    word boundary. Recursive, so long unpunctuated speech still yields readable cues.
    """
    text = " ".join(w["word"] for w in ph)
    if len(text) <= 2 * MAX_LINE - 2 or len(ph) < 2:
        return [ph]
    mid = len(text) / 2
    pos, acc = [], 0
    for i, w in enumerate(ph[:-1]):
        acc += len(w["word"]) + 1
        pos.append((i, acc))
    punct = [(i, c) for i, c in pos if re.search(r"[,;—\-]$", ph[i]["word"]) or ph[i + 1]["word"] in ("—",)]
    pool = [x for x in punct if abs(x[1] - mid) <= len(text) * 0.3] or pos
    k = min(pool, key=lambda x: abs(x[1] - mid))[0]
    return _split_long(ph[: k + 1]) + _split_long(ph[k + 1:])


def _units_from_phrases(phrases: list[list[dict]]) -> list[dict]:
    """One unit per spoken phrase; long phrases split recursively to fit two lines."""
    units = []
    for ph in phrases:
        for g in _split_long(ph):
            units.append({"start": g[0]["start"], "end": g[-1]["end"], "words": g,
                          "text": " ".join(w["word"] for w in g),
                          "sentence_end": bool(re.search(r'[.!?]["”]?$', g[-1]["word"]))})
    return units


def refine_cues(phrases: list[list[dict]]) -> list[dict]:
    """Phrase-locked caption cues.

    Merge rule: append the next unit when the result still fits two lines and
    either (a) the current cue has not ended its sentence, or (b) the current cue
    is a complete sentence shorter than MIN_CUE_S (then each sentence gets its own
    line). Never merge across a pause longer than 0.8 s.
    """
    cues = []
    for u in _units_from_phrases(phrases):
        if cues:
            c = cues[-1]
            joined = c["text"] + " " + u["text"]
            fits = len(joined) <= 2 * MAX_LINE - 2 and u["end"] - c["start"] <= 4.5 and u["start"] - c["end"] < 0.8
            short_sentence = c["sentence_end"] and (c["end"] - c["start"]) < MIN_CUE_S and len(c["parts"]) == 1                 and len(c["text"]) <= MAX_LINE + 4 and len(u["text"]) <= MAX_LINE + 4
            if fits and (not c["sentence_end"] or short_sentence):
                if c["sentence_end"]:
                    c["parts"].append(u["text"])
                else:
                    c["parts"][-1] = c["parts"][-1] + " " + u["text"]
                c.update(end=u["end"], words=c["words"] + u["words"], text=joined, sentence_end=u["sentence_end"])
                continue
        cues.append({**u, "parts": [u["text"]]})
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["start"] - 0.04 if i + 1 < len(cues) else c["end"] + LINGER_S
        c["display_end"] = round(min(nxt, c["end"] + LINGER_S), 3)
        c["lines"] = c["parts"] if len(c["parts"]) == 2 else _balance(c["parts"][0])
    return cues


def _ts(t: float, sep: str) -> str:
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"


def write_captions(cues: list[dict], tdir: Path) -> None:
    srt, vtt = [], ["WEBVTT", ""]
    for i, c in enumerate(cues, 1):
        srt += [str(i), f"{_ts(c['start'], ',')} --> {_ts(c['display_end'], ',')}", *c["lines"], ""]
        vtt += [f"{_ts(c['start'], '.')} --> {_ts(c['display_end'], '.')}", *c["lines"], ""]
    (tdir / "captions.srt").write_text("\n".join(srt), encoding="utf-8")
    (tdir / "captions.vtt").write_text("\n".join(vtt), encoding="utf-8")
    vm_env.write_json(tdir / "captions.json", cues)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--audio", required=True)
    ap.add_argument("--title", default=None)
    ap.add_argument("--language", default=None, help="ISO code; omit to auto-detect")
    ap.add_argument("--model", default="small", help="faster-whisper size: tiny|base|small|medium (CPU: small)")
    ap.add_argument("--pipeline", default="voiceover-film")
    ap.add_argument("--corrections", help="JSON {replacements:[{start, from, to, reason}]} applied to ASR words (logged)")
    ap.add_argument("--reuse-transcript", action="store_true", help="skip ASR if transcript/transcript.json exists")
    args = ap.parse_args()

    src = Path(args.audio).expanduser().resolve()
    vm_env.ensure_openmontage_on_path()
    from lib.checkpoint import init_project

    if not src.exists():
        print(f"BLOCKED: audio not found: {src}")
        return 2
    proj = init_project(args.project, title=args.title or args.project, pipeline_type=args.pipeline)
    for sub in vm_env.PROJECT_SUBDIRS:
        (proj / sub).mkdir(parents=True, exist_ok=True)

    # 1. inspect
    probe = vm_env.ffprobe(src)
    a_streams = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if not a_streams:
        print("BLOCKED: no audio stream in input")
        return 2
    report = {
        "source": str(src),
        "codec": a_streams[0].get("codec_name"),
        "sample_rate": int(a_streams[0].get("sample_rate", 0)),
        "channels": a_streams[0].get("channels"),
        "duration_s": float(probe["format"]["duration"]),
        "loudness": vm_env.loudness(src),
        "silences": silence_map(src),
        "clipping_ratio": clipping_ratio(src),
    }
    report["warnings"] = []
    if report["clipping_ratio"] > 0.001:
        report["warnings"].append(f"clipping in {report['clipping_ratio']:.2%} of samples")
    if report["loudness"].get("integrated_lufs", -99) < -35:
        report["warnings"].append("very quiet recording")
    long_sil = [s for s in report["silences"] if s["duration"] > 3]
    if long_sil:
        report["warnings"].append(f"{len(long_sil)} silences longer than 3 s")

    # 2. immutable copy
    dst = proj / "input" / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
    digest = vm_env.sha256(dst)
    if digest != vm_env.sha256(src):
        print("FAILED: copy checksum mismatch")
        return 1
    try:
        dst.chmod(0o444)
    except OSError:
        pass
    vm_env.write_json(proj / "input" / "SOURCE.json", {"original": str(src), "copy": str(dst), "sha256": digest,
                                                     "note": "immutable source; never edit in place"})
    report["sha256"] = digest
    vm_env.write_json(proj / "qa" / "audio_input_report.json", report)

    # 3. transcribe via OpenMontage tool
    raw_path = proj / "transcript" / "transcript.raw.json"
    if args.reuse_transcript and raw_path.exists():
        data = vm_env.read_json(raw_path)
    else:
        from tools.analysis.transcriber import Transcriber
        tr_in = {"input_path": str(dst), "model_size": args.model, "output_dir": str(proj / "transcript")}
        if args.language:
            tr_in["language"] = args.language
        res = Transcriber().execute(tr_in)
        if not res.success:
            print(f"FAILED: transcriber: {res.error}")
            return 1
        data = res.data
        vm_env.write_json(raw_path, data)  # untouched ASR output, kept for audit

    applied = []
    if args.corrections:
        corr = vm_env.read_json(Path(args.corrections))
        for fix in corr.get("replacements", []):
            hit = False
            for seg in data.get("segments", []):
                for w in seg.get("words", []) or []:
                    if w["word"].strip() == fix["from"] and abs(float(w["start"]) - float(fix["start"])) < 0.15:
                        lead = w["word"][: len(w["word"]) - len(w["word"].lstrip())]
                        w["word"] = lead + fix["to"]
                        hit = True
                if hit:
                    seg["text"] = "".join(w["word"] for w in seg.get("words", [])).strip()
                    break
            applied.append({**fix, "applied": hit})
        vm_env.write_json(proj / "transcript" / "corrections_applied.json", applied)
    vm_env.write_json(proj / "transcript" / "transcript.json", data)

    # 4. words, uncertainty, phrases
    words = []
    for seg in data.get("segments", []):
        for w in seg.get("words", []) or []:
            words.append({"word": w["word"].strip(), "start": round(float(w["start"]), 3),
                          "end": round(float(w["end"]), 3), "prob": round(float(w.get("probability", 1.0)), 3)})
    if not words:
        print("FAILED: no word timestamps produced")
        return 1
    review = [w for w in words if w["prob"] < LOW_CONF]
    phrases, cur = [], [words[0]]
    for prev, w in zip(words, words[1:]):
        gap = w["start"] - prev["end"]
        if gap >= PHRASE_GAP_S or re.search(r"[.!?]$", prev["word"]):
            phrases.append(cur)
            cur = []
        cur.append(w)
    phrases.append(cur)
    phrase_rows = []
    for i, ph in enumerate(phrases):
        nxt = phrases[i + 1][0]["start"] if i + 1 < len(phrases) else None
        phrase_rows.append({
            "id": f"P{i + 1:02d}",
            "text": " ".join(w["word"] for w in ph),
            "start": ph[0]["start"],
            "end": ph[-1]["end"],
            "pause_after": round(nxt - ph[-1]["end"], 3) if nxt else None,
            "sentence_end": bool(re.search(r"[.!?]$", ph[-1]["word"])),
            "min_prob": min(w["prob"] for w in ph),
        })
    vm_env.write_json(proj / "transcript" / "words.json", {"language": data.get("language"), "words": words,
                                                         "low_confidence_review": review})
    vm_env.write_json(proj / "transcript" / "phrases.json", phrase_rows)

    # 5. captions: phrase-locked cues (SRT/VTT/JSON); the burned-in track uses the same JSON
    cues = refine_cues(phrases)
    write_captions(cues, proj / "transcript")
    print(vm_env.json.dumps({
        "project_dir": str(proj), "duration_s": report["duration_s"], "language": data.get("language"),
        "words": len(words), "phrases": len(phrase_rows), "low_confidence_words": [w["word"] for w in review],
        "loudness": report["loudness"], "warnings": report["warnings"], "corrections": applied,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

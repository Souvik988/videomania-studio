"""Independent QA instrument for a rendered video. Measures; never self-certifies.

Usage:
  qa.py --project ID --video PATH [--tag draft|final] [--font FONT.woff2]

Writes projects/<ID>/qa/<tag>/:
  technical_report.json   ffprobe streams, duration vs plan, black/freeze detection, motion stats
  audio_report.json       loudness/true peak, silences, music-audible-in-gaps, A/V offset + drift
  caption_report.json     SRT/VTT structure, reading speed, line length, glyph coverage
  contact_sheet.png       one labelled frame per scene midpoint
  phone_preview.png       frames at 360 px wide (phone-size legibility check)
  strips/<Sxx>-<Syy>.png  five frames around every scene boundary
  summary.json            PASS/FAIL per gate (subjective quality is NOT scored here)
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


def frame_at(video: Path, t: float, width: int | None = None):
    from PIL import Image
    import io
    vf = [f"scale={width}:-2:flags=lanczos"] if width else []
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1"]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-f", "image2pipe", "-vcodec", "png", "-"]
    exe = vm_env.shutil.which("ffmpeg") if hasattr(vm_env, "shutil") else "ffmpeg"
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(out)).convert("RGB")


def label(img, text: str):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, 34], fill=(0, 0, 0))
    d.text((8, 8), text, fill=(255, 255, 255))
    return img


def grid(images, cols: int, pad: int = 8, bg=(30, 30, 30)):
    from PIL import Image
    w, h = images[0].size
    rows = (len(images) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * h + (rows + 1) * pad), bg)
    for i, im in enumerate(images):
        r, c = divmod(i, cols)
        sheet.paste(im, (pad + c * (w + pad), pad + r * (h + pad)))
    return sheet


def gray_frames(video: Path, w: int = 108, h: int = 192, fps: int = 30):
    import numpy as np
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={w}:{h},format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.uint8).reshape(-1, h, w).astype(np.float32)


def detect(video: Path, filt: str, key: str) -> list[dict]:
    p = vm_env.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf" if "detect" in filt and "silence" not in filt else "-af",
                    filt, "-f", "null", "-"], check=False)
    events, cur = [], {}
    for line in p.stderr.splitlines():
        for k, v in re.findall(rf"({key}_(?:start|end|duration)):\s*([\d.]+)", line):
            cur[k.split("_")[-1]] = float(v)
            if "end" in cur and "start" in cur:
                events.append(cur)
                cur = {}
    if cur.get("start") is not None and "end" not in cur:
        cur["end"] = None
        events.append(cur)
    return events


def audio_array(path: Path, sr: int = 16000, start: float = 0.0, dur: float | None = None):
    import numpy as np
    # Only seek when needed: input-side -ss bypasses the MP4 edit list that
    # compensates AAC encoder priming (1024 samples), which fakes a ~21 ms offset.
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{start:.3f}"] if start > 0 else []) + ["-i", str(path)]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32)


def xcorr_offset(a, b, sr: int, max_ms: int = 300) -> float:
    import numpy as np
    n = min(len(a), len(b))
    a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    m = int(sr * max_ms / 1000)
    fa = np.fft.rfft(a, 2 * n)
    fb = np.fft.rfft(b, 2 * n)
    cc = np.fft.irfft(fa * np.conj(fb))
    cc = np.concatenate([cc[-m:], cc[: m + 1]])
    return (int(np.argmax(cc)) - m) / sr * 1000.0


def rms_db(x) -> float:
    import numpy as np
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-9)) if len(x) else -120.0


def parse_srt(path: Path) -> list[dict]:
    def ts(x):
        h, m, s = x.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    cues = []
    for block in path.read_text(encoding="utf-8").strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = [ts(x.strip()) for x in lines[1].split("-->")]
            cues.append({"start": a, "end": b, "lines": lines[2:], "text": " ".join(lines[2:])})
    return cues


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--video", required=True)
    ap.add_argument("--tag", default="draft")
    ap.add_argument("--font", default=None, help="caption font file for glyph-coverage check")
    ap.add_argument("--expect", default="1080x1920@30")
    ap.add_argument("--caption-zone", default=None, help="caption band top,bottom as fractions (default 0.70,0.84 portrait / 0.78,0.95 landscape)")
    ap.add_argument("--text-colors", default="#fffaf2,#ffffff,#ffc23d,#ff7a66", help="caption text colours, incl. accents")
    ap.add_argument("--caption-font-px", type=int, default=52)
    ap.add_argument("--allow-holds", default="", help="deliberate story holds that may be still, e.g. '20.0-22.5,60-64'")
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()
    import numpy as np

    proj = vm_env.project_dir(args.project)
    video = Path(args.video).resolve()
    out = proj / "qa" / args.tag
    (out / "strips").mkdir(parents=True, exist_ok=True)
    scenes = vm_env.read_json(proj / "artifacts" / "scene_plan.json")["scenes"]
    plan_end = max(s["end_seconds"] for s in scenes)
    gates: dict[str, dict] = {}

    # ---------------- technical
    pr = vm_env.ffprobe(video)
    v = next((s for s in pr["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in pr["streams"] if s["codec_type"] == "audio"), None)
    dur = float(pr["format"]["duration"])
    ew, eh = map(int, args.expect.split("@")[0].split("x"))
    efps = float(args.expect.split("@")[1])
    fps = eval(v["avg_frame_rate"]) if v else 0  # noqa: S307 - ffprobe rational like 30/1
    tech = {
        "path": str(video), "size_bytes": int(pr["format"]["size"]), "duration_s": dur, "planned_end_s": plan_end,
        "video": {k: v.get(k) for k in ("codec_name", "width", "height", "pix_fmt", "avg_frame_rate", "nb_frames", "color_space", "color_transfer")} if v else None,
        "audio": {k: a.get(k) for k in ("codec_name", "sample_rate", "channels", "bit_rate")} if a else None,
    }
    gates["has_video_and_audio"] = {"pass": bool(v and a)}
    gates["dimensions_fps"] = {"pass": bool(v and v["width"] == ew and v["height"] == eh and abs(fps - efps) < 0.01),
                               "observed": f"{v and v['width']}x{v and v['height']}@{fps:.3f}"}
    gates["codecs"] = {"pass": bool(v and v["codec_name"] == "h264" and v.get("pix_fmt") == "yuv420p" and a and a["codec_name"] == "aac"),
                       "observed": f"{v and v['codec_name']}/{v and v.get('pix_fmt')} + {a and a['codec_name']}"}
    gates["duration_matches_plan"] = {"pass": abs(dur - plan_end) <= 0.2, "observed": round(dur, 3), "planned": plan_end}
    black = detect(video, "blackdetect=d=0.25:pix_th=0.03", "black")
    tech["black_segments"] = black
    gates["no_unintended_black"] = {"pass": not black, "observed": black}
    freezes = detect(video, "freezedetect=n=0.0008:d=2.5", "freeze")
    tech["freeze_segments"] = freezes
    gates["no_long_freezes"] = {"pass": all((f.get("start", 0) >= dur - 3.0) for f in freezes), "observed": freezes,
                                "note": "a freeze in the final 3 s is the planned end hold"}

    # Motion is "something visibly changed": >= 12 pixels at 270x480 moved by > 6
    # grey levels between consecutive frames. Mean-difference metrics are blind to
    # a thin line or a small dot moving across a dark field, so they are not used.
    g = gray_frames(video, 270, 480)
    absd = np.abs(np.diff(g, axis=0))
    changed_px = (absd > 6).sum(axis=(1, 2))
    diffs = absd.mean(axis=(1, 2))
    flat = g.std(axis=(1, 2)) < 1.0
    still = changed_px < 12
    runs, cur = [], 0
    for i, s in enumerate(still):
        if s:
            cur += 1
        else:
            if cur:
                runs.append((i - cur, cur))
            cur = 0
    if cur:
        runs.append((len(still) - cur, cur))
    long_runs = [{"start_s": round(st / 30, 2), "length_s": round(n / 30, 2)} for st, n in runs if n / 30 > 0.6]
    end_hold = round(runs[-1][1] / 30, 2) if runs and runs[-1][0] + runs[-1][1] >= len(still) - 1 else 0.0
    tech["motion"] = {
        "frames_analyzed": int(len(g)), "changing_frame_ratio": round(float((~still).mean()), 3),
        "flat_frame_ratio": round(float(flat.mean()), 3), "still_runs_over_0p6s": long_runs, "end_hold_s": end_hold,
        "mean_frame_delta": round(float(diffs.mean()), 3), "median_changed_px": int(np.median(changed_px)),
    }
    over = [r for r in long_runs if r["length_s"] > 1.5 and r["start_s"] + r["length_s"] < len(still) / 30 - 0.1]
    gates["not_a_slideshow"] = {"pass": float((~still).mean()) >= 0.7 and not over, "observed": {"changing_frame_ratio": tech["motion"]["changing_frame_ratio"], "still_runs_over_1p5s": over},
                                "note": "motionmaxxing-derived: >= 70% of frames change; no still stretch > 1.5 s except the end hold"}
    gates["end_hold"] = {"pass": end_hold <= 2.0, "observed": end_hold, "note": "final hold <= 2.0 s (CTA read time)"}
    gates["no_dead_frames"] = {"pass": float(flat.mean()) < 0.02, "observed": tech["motion"]["flat_frame_ratio"]}
    vm_env.write_json(out / "technical_report.json", tech)

    # ---------------- audio
    aud: dict = {}
    if a:
        aud["loudness"] = vm_env.loudness(video)
        aud["silences_gt_1s"] = detect(video, "silencedetect=noise=-50dB:d=1.0", "silence")
        L = aud["loudness"]
        gates["loudness"] = {"pass": -16.0 <= L.get("integrated_lufs", -99) <= -12.0 and L.get("true_peak_dbtp", 9) <= -1.5,
                             "observed": L, "target": "-14 LUFS ±2 (social), true peak <= -1.5 dBTP measured on the encoded file"}
        gates["no_accidental_silence"] = {"pass": all((s.get("start") or 0) >= dur - 1.6 for s in aud["silences_gt_1s"]),
                                          "observed": aud["silences_gt_1s"]}
        sr = 16000
        mixed = audio_array(video, sr)
        mix_ref = proj / "audio" / "mix.wav"
        voice = proj / "audio" / "stems" / "voice.wav"
        if mix_ref.exists():
            ref = audio_array(mix_ref, sr)
            off_start = xcorr_offset(mixed[: sr * 8], ref[: sr * 8], sr)
            s2 = max(0, int((dur - 9) * sr))
            off_end = xcorr_offset(mixed[s2: s2 + sr * 8], ref[s2: s2 + sr * 8], sr)
            aud["av_offset_ms"] = {"start": round(off_start, 2), "end": round(off_end, 2), "drift_ms": round(off_end - off_start, 2)}
            gates["audio_sync"] = {"pass": abs(off_start) <= 22 and abs(off_end - off_start) <= 22, "observed": aud["av_offset_ms"],
                                   "note": "render audio vs master mix, cross-correlation; <= 22 ms (~2/3 frame)"}
        phrases = vm_env.read_json(proj / "transcript" / "phrases.json")
        gaps = [(p["end"] + 0.08, p["end"] + p["pause_after"] - 0.08) for p in phrases if p.get("pause_after") and p["pause_after"] >= 0.4]
        if voice.exists() and gaps:
            vo = audio_array(voice, sr)
            gm = np.concatenate([mixed[int(x * sr): int(y * sr)] for x, y in gaps])
            gv = np.concatenate([vo[int(x * sr): int(y * sr)] for x, y in gaps])
            aud["speech_gaps"] = {"count": len(gaps), "total_s": round(sum(y - x for x, y in gaps), 2),
                                  "render_rms_dbfs": round(rms_db(gm), 1), "voice_stem_rms_dbfs": round(rms_db(gv), 1)}
            speech = np.concatenate([mixed[int(p["start"] * sr): int(p["end"] * sr)] for p in phrases])
            aud["speech_rms_dbfs"] = round(rms_db(speech), 1)
            music_ok = rms_db(gm) > -45 and rms_db(gm) > rms_db(gv) + 6
            gates["music_audible"] = {"pass": bool(music_ok), "observed": aud["speech_gaps"],
                                      "note": "in narration pauses the render must carry clearly more signal than the voice stem alone"}
            gap_vs_speech = rms_db(speech) - rms_db(gm)
            aud["speech_over_bed_db"] = round(gap_vs_speech, 1)
            gates["voice_forward"] = {"pass": gap_vs_speech >= 6.0, "observed": round(gap_vs_speech, 1),
                                      "note": "speech-segment RMS minus pause RMS; >= 6 dB keeps VO in front of the bed"}
        # stereo image: a stereo score must survive the mix (mono collapse is a defect)
        st = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "2", "-ar", str(sr), "-f", "f32le", "-"],
                            capture_output=True, check=True).stdout
        lr = np.frombuffer(st, dtype=np.float32).reshape(-1, 2)
        side_db = rms_db((lr[:, 0] - lr[:, 1]) / 2) - rms_db((lr[:, 0] + lr[:, 1]) / 2)
        aud["stereo"] = {"channels": a.get("channels"), "side_minus_mid_db": round(side_db, 1)}
        music_stem = proj / "audio" / "stems" / "music.wav"
        if music_stem.exists() and vm_env.ffprobe(music_stem)["streams"][0].get("channels") == 2:
            gates["stereo_image"] = {"pass": a.get("channels") == 2 and side_db > -40, "observed": aud["stereo"],
                                     "note": "stereo music must not collapse to dual-mono (side energy > -40 dB re mid)"}
        aud["method"] = "measured (ffmpeg ebur128/silencedetect + numpy RMS + FFT cross-correlation); no listening was performed"
    vm_env.write_json(out / "audio_report.json", aud)

    # ---------------- captions
    cap: dict = {}
    srt = proj / "transcript" / "captions.srt"
    vtt = proj / "transcript" / "captions.vtt"
    if srt.exists():
        cues = parse_srt(srt)
        overlaps = [i for i in range(1, len(cues)) if cues[i]["start"] < cues[i - 1]["end"] - 1e-3]
        fast = [f'{c["text"]} ({len(c["text"]) / max(0.01, c["end"] - c["start"]):.1f} cps)' for c in cues if len(c["text"]) / max(0.01, c["end"] - c["start"]) > 20]
        short = [c["text"] for c in cues if c["end"] - c["start"] < 0.6]
        long_lines = [l for c in cues for l in c["lines"] if len(l) > 42]
        sentence_straddle = [c["text"] for c in cues if any(re.search(r"[.!?]\s+\S", l) for l in c["lines"])]
        cap.update({"cues": len(cues), "overlaps": overlaps, "cps_over_20": fast, "shorter_than_0p6s": short,
                    "lines_over_42": long_lines, "cues_straddling_sentences": sentence_straddle,
                    "vtt_exists": vtt.exists() and vtt.read_text(encoding="utf-8").startswith("WEBVTT")})
        if args.font:
            from fontTools.ttLib import TTFont
            cmap = TTFont(args.font).getBestCmap()
            chars = sorted({ch for c in cues for ch in c["text"] if not ch.isspace()})
            missing = [ch for ch in chars if ord(ch) not in cmap]
            cap["glyph_coverage"] = {"font": args.font, "missing": missing}
        gates["captions_structure"] = {"pass": not overlaps and not long_lines and cap["vtt_exists"] and not sentence_straddle,
                                       "observed": {k: cap[k] for k in ("overlaps", "lines_over_42", "cues_straddling_sentences", "vtt_exists")}}
        gates["captions_reading_speed"] = {"pass": not fast, "observed": {"cps_over_20": fast, "warn_short": short}}
        if "glyph_coverage" in cap:
            gates["caption_glyphs"] = {"pass": not cap["glyph_coverage"]["missing"], "observed": cap["glyph_coverage"]["missing"]}
    vm_env.write_json(out / "caption_report.json", cap)

    # ---------------- caption contrast on the rendered pixels (never white on light)
    cue_src = next((p for p in (proj / "source" / "data.js", proj / "transcript" / "captions.json") if p.exists()), None)
    if cue_src is not None:
        portrait = bool(v and v["height"] > v["width"])
        zone = args.caption_zone or ("0.70,0.84" if portrait else "0.78,0.95")
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("caption_contrast.py")), "--video", str(video),
                            "--cues", str(cue_src), "--zone", zone, "--text-colors", args.text_colors,
                            "--font-px", str(args.caption_font_px), "--out", str(out / "caption_contrast.json")],
                           capture_output=True, text=True)
        cc = vm_env.read_json(out / "caption_contrast.json") if (out / "caption_contrast.json").exists() else {"pass": False, "error": r.stderr[-400:]}
        gates["caption_contrast"] = {"pass": bool(cc.get("pass")), "observed": {"worst": cc.get("worst"), "fail": cc.get("fail"),
                                     "not_found_at": cc.get("not_found_at")},
                                     "note": "WCAG >= 4.5:1 per letter against its real background; every not_found time must be a deliberate caption suppression"}

    # ---------------- cadence: shot lengths and stretches with no visible change
    from analyze_video import analyze
    portrait = bool(v and v["height"] > v["width"])
    band = tuple(float(x) for x in (args.caption_zone or ("0.70,0.84" if portrait else "0.78,0.95")).split(","))
    av = analyze(video, out / "analysis", sheets=False, ignore_band=band, hold_tail=3.0)
    holds = [tuple(float(x) for x in h.split("-")) for h in args.allow_holds.split(",") if h.strip()]
    dead = [d for d in av["dead_stretches_over_1p5s"]
            if d["seconds"] > 2.2 and not any(h0 - 0.1 <= d["start"] and d["end"] <= h1 + 0.1 for h0, h1 in holds)]
    gates["cadence"] = {"pass": not dead, "observed": {"dead_over_2p2s": dead, "shots": {k: av["shots"][k] for k in ("count", "mean_s", "median_s", "max_s")},
                        "visual_events": av["visual_events"]},
                        "note": "no stretch over 2.2 s without a visible change outside declared story holds (--allow-holds); captions band ignored"}

    # ---------------- story: open-loop ledger (written in step 2)
    ledger = proj / "storyboard" / "open_loops.json"
    if ledger.exists():
        from open_loops import narration_text, validate
        ol = validate(vm_env.read_json(ledger), narration_text(proj), dur, None)
        gates["open_loops"] = {"pass": ol["pass"], "observed": ol["problems"]}
    else:
        gates["open_loops"] = {"pass": False, "observed": "storyboard/open_loops.json missing (templates/open_loops.json)"}

    # ---------------- visual sheets
    from PIL import Image
    mids = [(s["id"], (s["start_seconds"] + s["end_seconds"]) / 2) for s in scenes]
    sheet = [label(frame_at(video, t, 360), f"{sid} {t:.2f}s") for sid, t in mids]
    grid(sheet, 5).save(out / "contact_sheet.png")
    phone_t = [round(dur * k / 7, 1) for k in range(1, 7)]
    phone = [label(frame_at(video, t, 360), f"{t:.1f}s @360px") for t in phone_t]
    grid(phone, 6).save(out / "phone_preview.png")
    # the first 2.5 s decide whether anyone stays: every quarter second, full detail
    opening = [label(frame_at(video, t, 270), f"{t:.2f}s") for t in [i * 0.25 for i in range(11)]]
    grid(opening, 6, pad=4).save(out / "opening_2p5s.png")
    for i in range(len(scenes) - 1):
        b = scenes[i]["end_seconds"]
        fr = [label(frame_at(video, max(0, t), 216), f"{t:.2f}s") for t in (b - 0.3, b - 0.15, b, b + 0.15, b + 0.3)]
        grid(fr, 5, pad=4).save(out / "strips" / f"{scenes[i]['id']}-{scenes[i + 1]['id']}.png")

    summary = {"video": str(video), "tag": args.tag, "gates": {k: v["pass"] for k, v in gates.items()},
               "all_technical_gates_pass": all(v["pass"] for v in gates.values()), "details": gates,
               "artifacts": {"contact_sheet": str(out / "contact_sheet.png"), "phone_preview": str(out / "phone_preview.png"),
                             "opening": str(out / "opening_2p5s.png"), "analysis": str(out / "analysis" / "report.txt"),
                             "strips": str(out / "strips")}}
    vm_env.write_json(out / "summary.json", summary)
    print(json.dumps({"all_technical_gates_pass": summary["all_technical_gates_pass"], "gates": summary["gates"]}, indent=2))
    return 0 if summary["all_technical_gates_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Break any video (a reel the user admires, or our own render) into numbers to design against.

Usage:
  analyze_video.py VIDEO --out DIR [--sheet-fps 6] [--bpm 128 --phase 0.0] [--hold-tail 3.0]

Writes to DIR:
  sheet_NN.png        4x4 contact sheets, --sheet-fps tiles per second
  analysis.json       cuts, shot lengths, visual events, dead stretches, luminance, RMS, onsets
  report.txt          the same, readable

What it measures:
  hard cuts           frames where most of the picture changes at once (mean abs diff > 40/255)
  shot lengths        intervals between hard cuts: mean, median, p90, max (house reels: 1.1–1.4 s, max ~2.8 s)
  visual events       frames with a visible change (diff > 6/255); motion-graphics films change
                      by morphs and moves, not only by cuts, so cadence is judged on events
  dead stretches      runs over 1.5 s with no visual event (the final --hold-tail seconds excluded)
  luminance / RMS     every 0.5 s / 0.25 s; audio onsets (energy rises > mean + 2.5 sd)
  beat offsets        with --bpm, how far each cut sits from the nearest beat and half beat

Ported from motion-showreel/scripts/analyze-reference.mjs in Nate Herk's herk-edit-kit
(MIT, https://github.com/nateherkai/herk-edit-kit); extended with shot statistics, visual
events and dead stretches for Video Mania's QA. Needs ffmpeg/ffprobe and numpy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

CUT_DIFF = 40.0     # mean abs luma diff (0-255) at 64x36 that counts as a hard cut
PIX_DIFF = 12       # a pixel "changed" when its luma moves more than this (above grain noise)
EVENT_FRAC = 0.004  # a frame is a visible event when > 0.4 % of pixels changed (a word-sized change)
DEAD_S = 1.5        # a stretch longer than this with no visible change is reported


def run(cmd: list[str]) -> bytes:
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {p.stderr.decode(errors='replace')[:400]}")
    return p.stdout


def video_fps(video: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
             "-of", "csv=p=0", str(video)]).decode().strip()
    num, den = (r.split("/") + ["1"])[:2]
    return float(num) / float(den or 1)


def analyze(video: Path, out: Path, sheet_fps: float = 6, bpm: float = 0, phase: float = 0,
            hold_tail: float = 3.0, sheets: bool = True, ignore_band: tuple[float, float] | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    if sheets:
        run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
             f"fps={sheet_fps},scale=480:-2,tile=layout=4x4", str(out / "sheet_%02d.png")])
    fps = video_fps(video)
    W, H = 64, 36
    raw = run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"scale={W}:{H},format=gray",
               "-f", "rawvideo", "-"])
    frames = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
    n = len(frames)
    dur = n / fps
    lum = frames.mean(axis=(1, 2))
    diff = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2)) if n > 1 else np.zeros(0)

    cuts = [round((i + 1) / fps, 3) for i, d in enumerate(diff) if d > CUT_DIFF and (i == 0 or diff[i - 1] <= CUT_DIFF)]
    bounds = [0.0] + cuts + [dur]
    shots = [round(b - a, 3) for a, b in zip(bounds, bounds[1:]) if b - a > 1e-6]

    # visible events at higher resolution: share of pixels that changed, optionally
    # ignoring a horizontal band (the caption zone, so caption highlights do not mask dead graphics)
    EH = 192
    raw2 = run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"scale=-2:{EH},format=gray", "-f", "rawvideo", "-"])
    EW = len(raw2) // (n * EH) if n else 0
    big = np.frombuffer(raw2[: n * EH * EW], np.uint8).reshape(-1, EH, EW).astype(np.int16)
    keep = np.ones(EH, bool)
    if ignore_band:
        keep[int(ignore_band[0] * EH): int(ignore_band[1] * EH)] = False
    big = big[:, keep, :]
    frac = (np.abs(np.diff(big, axis=0)) > PIX_DIFF).mean(axis=(1, 2)) if len(big) > 1 else np.zeros(0)
    event = frac > EVENT_FRAC
    tail_start = max(0.0, dur - hold_tail)
    dead, run_start = [], None
    for i, e in enumerate(event):
        t = (i + 1) / fps
        if not e and run_start is None:
            run_start = t
        if (e or i == len(event) - 1) and run_start is not None:
            end = t
            if end - run_start > DEAD_S and run_start < tail_start:
                dead.append({"start": round(run_start, 2), "end": round(min(end, tail_start), 2),
                             "seconds": round(min(end, tail_start) - run_start, 2)})
            run_start = None
    events_per_s = float(event.sum()) / dur if dur else 0.0

    res: dict = {
        "video": str(video), "fps": round(fps, 3), "frames": n, "duration_s": round(dur, 3),
        "hard_cuts_s": cuts,
        "shots": {"count": len(shots), "mean_s": round(float(np.mean(shots)), 3) if shots else None,
                  "median_s": round(float(np.median(shots)), 3) if shots else None,
                  "p90_s": round(float(np.percentile(shots, 90)), 3) if shots else None,
                  "max_s": max(shots) if shots else None, "lengths_s": shots},
        "visual_events": {"changing_frame_ratio": round(float(event.mean()), 3) if len(event) else 0.0,
                          "events_per_second": round(events_per_s, 2),
                          "ignored_band": list(ignore_band) if ignore_band else None},
        "dead_stretches_over_1p5s": dead,
        "luminance_every_0p5s": [round(float(lum[int(f)]), 1) for f in np.arange(0, n, max(1, round(fps / 2)))],
    }

    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "22050", "-f", "s16le", "-"],
                         capture_output=True)
    if pcm.returncode == 0 and pcm.stdout:
        x = np.frombuffer(pcm.stdout, np.int16).astype(np.float32) / 32768.0
        SR, HOP = 22050, 512
        m = len(x) // HOP
        e = np.sqrt((x[: m * HOP].reshape(m, HOP) ** 2).mean(axis=1)) if m else np.zeros(0)
        db = lambda v: round(float(20 * np.log10(v + 1e-9)), 1)  # noqa: E731
        res["rms_db_every_0p25s"] = [db(e[min(len(e) - 1, int(t * SR / HOP))]) for t in np.arange(0, len(x) / SR - 0.05, 0.25)] if len(e) else []
        on = np.maximum(0, np.diff(e))
        if len(on) > 2:
            thr = on.mean() + 2.5 * on.std()
            res["onsets_s"] = [round((p + 1) * HOP / SR, 2) for p in range(1, len(on) - 1)
                               if on[p] > thr and on[p] >= on[p - 1] and on[p] >= on[p + 1]]
    else:
        res["audio"] = "no audio stream"

    if bpm:
        P = 60.0 / bpm
        off = lambda c, q: ((((c - phase + q / 2) % q) + q) % q) - q / 2  # noqa: E731
        res["beat"] = {"bpm": bpm, "period_s": round(P, 4), "phase_s": phase,
                       "cut_offset_beat_ms": [round(off(c, P) * 1000) for c in cuts],
                       "cut_offset_half_beat_ms": [round(off(c, P / 2) * 1000) for c in cuts]}

    (out / "analysis.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
    sh = res["shots"]
    lines = [f"{video.name}: {dur:.2f} s at {fps:g} fps, {n} frames",
             f"hard cuts: {len(cuts)}  shots mean {sh['mean_s']} s, median {sh['median_s']} s, p90 {sh['p90_s']} s, max {sh['max_s']} s",
             f"visual events: {res['visual_events']['changing_frame_ratio']*100:.0f}% of frames change visibly "
             f"({res['visual_events']['events_per_second']}/s)",
             "dead stretches > 1.5 s (end hold excluded): " + (", ".join(f"{d['start']}-{d['end']}s" for d in dead) or "none"),
             "hard cuts (s): " + " ".join(f"{c:.2f}" for c in cuts)]
    if "onsets_s" in res:
        lines.append("audio onsets (s): " + " ".join(f"{o:.2f}" for o in res["onsets_s"][:80]))
    if bpm:
        lines.append("cut offset from nearest beat (ms): " + " ".join(f"{o:+d}" for o in res["beat"]["cut_offset_beat_ms"]))
    (out / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet-fps", type=float, default=6)
    ap.add_argument("--bpm", type=float, default=0)
    ap.add_argument("--phase", type=float, default=0)
    ap.add_argument("--hold-tail", type=float, default=3.0, help="seconds at the end treated as a deliberate hold")
    ap.add_argument("--no-sheets", action="store_true")
    ap.add_argument("--ignore-band", help="top,bottom as fractions of height to ignore for events, e.g. 0.71,0.82 (captions)")
    a = ap.parse_args()
    band = tuple(float(v) for v in a.ignore_band.split(",")) if a.ignore_band else None
    analyze(Path(a.video).resolve(), Path(a.out).resolve(), a.sheet_fps, a.bpm, a.phase, a.hold_tail, not a.no_sheets, band)
    sys.stdout.reconfigure(encoding="utf-8")
    print((Path(a.out) / "report.txt").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

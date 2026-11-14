"""Understand music before scoring with it: tempo, beat and bar grid, key and mode, energy per bar,
sections, the biggest hits, and a plain-words character for each track.

    python music_map.py <track.mp3> [<track2> ...] -o audio/music_map.json [--sheet audio/music_map.png]

Why: the director film's score failed when music was "just put behind". Scoring means choosing a track for
what the scene feels like, entering on a downbeat at a section start, cutting on the bar, landing picture
hits on the music's hits, and leaving silence (a cappella) where the words must stand alone.
See references/audio-cinematography.md for how to use the map.

Output per track:
  duration, bpm, beat_times, downbeats (bar starts), key ("G major"), energy_per_bar (0-1),
  sections [{start, end, energy, label}], hits [{t, strength}], entries (bar starts that open a section
  or follow a quiet bar: the places a track can come in cleanly), character (words for the director).
Reads in one pass; never claims to have heard the music.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

try:
    import librosa
except ImportError:  # pragma: no cover
    sys.exit("music_map.py needs librosa: python -m uv pip install --python <venv python> librosa")

MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def key_of(chroma: np.ndarray) -> tuple[str, str]:
    c = chroma.mean(axis=1)
    best = max(((np.corrcoef(np.roll(prof, k), c)[0, 1], NOTES[k], mode) for k in range(12)
                for prof, mode in ((MAJ, "major"), (MIN, "minor"))))
    return f"{best[1]} {best[2]}", best[2]


def analyse(path: Path, sr: int = 22050) -> dict:
    y, sr = librosa.load(str(path), sr=sr, mono=True)
    dur = len(y) / sr
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, units="frames")
    bpm = float(np.atleast_1d(tempo)[0])
    bt = librosa.frames_to_time(beats, sr=sr)
    # bar phase: the beat offset (0-3) whose beats carry the most onset strength
    if len(beats) >= 8:
        strength = onset[np.clip(beats, 0, len(onset) - 1)]
        phase = int(np.argmax([strength[k::4].mean() for k in range(4)]))
    else:
        phase = 0
    down = bt[phase::4]
    rms = librosa.feature.rms(y=y)[0]
    rt = librosa.frames_to_time(np.arange(len(rms)), sr=sr)
    bars = list(down) + [dur]
    e = np.array([rms[(rt >= a) & (rt < b)].mean() if np.any((rt >= a) & (rt < b)) else 0 for a, b in zip(bars, bars[1:])])
    en = (e / (e.max() or 1)).round(3)
    # sections: novelty on chroma + mfcc, snapped to bars
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    mf = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    feat = np.vstack([librosa.util.normalize(chroma, axis=1), librosa.util.normalize(mf, axis=1)])
    k = int(np.clip(round(dur / 22), 3, 12))
    bnd = librosa.segment.agglomerative(feat, k)
    bt_s = sorted(set([0.0] + [float(down[np.argmin(np.abs(down - t))]) if len(down) else t
                                for t in librosa.frames_to_time(bnd, sr=sr)] + [dur]))
    sections = []
    for a, b in zip(bt_s, bt_s[1:]):
        if b - a < 2:
            continue
        m = (rt >= a) & (rt < b)
        lv = float(rms[m].mean() / (rms.max() or 1)) if m.any() else 0
        sections.append({"start": round(a, 2), "end": round(b, 2), "energy": round(lv, 2)})
    if sections:
        q = np.percentile([s["energy"] for s in sections], [33, 66])
        for s in sections:
            s["label"] = "low" if s["energy"] < q[0] else "mid" if s["energy"] < q[1] else "high"
    # hits: strongest onsets, at least 1.5 s apart
    pk = librosa.util.peak_pick(onset, pre_max=10, post_max=10, pre_avg=30, post_avg=30, delta=0.5, wait=30)
    pt = librosa.frames_to_time(pk, sr=sr); ps = onset[pk] / (onset.max() or 1)
    hits = []
    for i in np.argsort(-ps):
        if all(abs(pt[i] - h["t"]) > 1.5 for h in hits):
            hits.append({"t": round(float(pt[i]), 2), "strength": round(float(ps[i]), 2)})
        if len(hits) >= 16:
            break
    hits.sort(key=lambda h: h["t"])
    entries = sorted({s["start"] for s in sections} | {round(float(down[i]), 2) for i in range(1, len(en)) if en[i - 1] < 0.35 and en[i] > 0.55})
    key, mode = key_of(chroma)
    cent = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    perc = librosa.effects.percussive(y[: sr * 60]); harm = librosa.effects.harmonic(y[: sr * 60])
    drive = float(np.sqrt(np.mean(perc ** 2)) / (np.sqrt(np.mean(harm ** 2)) + 1e-9))
    words = []
    words.append("fast, urgent" if bpm >= 140 else "driving" if bpm >= 115 else "walking pace" if bpm >= 90 else "slow, spacious")
    words.append("bright, open" if mode == "major" else "dark, tense")
    words.append("beat-led (drums carry it)" if drive > 0.6 else "melody-led (strings/keys carry it)")
    words.append("sparkly, high" if cent > 2600 else "warm, low-mid" if cent < 1700 else "full-range")
    dyn = float(en.max() - np.percentile(en, 20)) if len(en) else 0
    words.append("big build and drops" if dyn > 0.6 else "steady level")
    return {"file": path.name, "duration": round(dur, 2), "bpm": round(bpm, 1), "bar_seconds": round(240 / bpm, 3) if bpm else None,
            "key": key, "drive": round(drive, 2), "centroid_hz": round(cent), "character": ", ".join(words),
            "beat_times": [round(float(t), 3) for t in bt], "downbeats": [round(float(t), 3) for t in down],
            "energy_per_bar": en.tolist(), "sections": sections, "hits": hits, "entries": entries}


def sheet(maps: list[dict], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(maps), 1, figsize=(14, 1.9 * len(maps)), squeeze=False)
    for ax, m in zip(axs[:, 0], maps):
        d = m["downbeats"]; e = m["energy_per_bar"]
        ax.bar(d[: len(e)], e, width=m["bar_seconds"] or 1, align="edge", color="#e11d2e", alpha=0.7)
        for s in m["sections"]:
            ax.axvline(s["start"], color="#19c8b9", lw=1)
            ax.text(s["start"] + 0.3, 1.02, s["label"], fontsize=7, color="#19c8b9")
        for h in m["hits"]:
            ax.plot(h["t"], 0.98, "v", color="black", ms=4)
        ax.set_xlim(0, m["duration"]); ax.set_ylim(0, 1.12); ax.set_yticks([])
        ax.set_title(f"{m['file'][:60]} | {m['bpm']} bpm | {m['key']} | {m['character']}", fontsize=8, loc="left")
    fig.tight_layout(); fig.savefig(out, dpi=110)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tracks", nargs="+"); ap.add_argument("-o", "--out", required=True); ap.add_argument("--sheet")
    a = ap.parse_args()
    maps = []
    for t in a.tracks:
        m = analyse(Path(t)); maps.append(m)
        print(f"{m['file'][:58]:<58} {m['duration']:>6.1f}s {m['bpm']:>6.1f} bpm  {m['key']:<9} drive {m['drive']}")
        print(f"    {m['character']}")
        print("    sections: " + "  ".join(f"{s['start']:.1f}-{s['end']:.1f} {s['label']}" for s in m["sections"]))
        print("    hits: " + " ".join(f"{h['t']:.1f}" for h in m["hits"][:12]))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"tracks": maps}, indent=1), encoding="utf-8")
    if a.sheet:
        try:
            sheet(maps, Path(a.sheet))
        except ImportError:
            print("(no matplotlib: skipped the --sheet picture; the json has everything)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Audio -> mouth-shape (viseme) track for a coded talking character. CPU only, no downloads.

Usage:
  viseme_track.py --audio VO.wav --out talk.json [--fps 30] [--words words.json]
  viseme_track.py --rhubarb rhubarb_out.json --out talk.json [--audio VO.wav]

Output (talk.json):
  {"fps":30, "duration":s, "source":"estimate"|"rhubarb",
   "cues":[{"t0":s,"t1":s,"v":"X|A|B|C|D|E|F|G|H"}...],   # mouth shapes, Preston Blair / Rhubarb letters
   "env":[0..1 per frame],                                  # smoothed loudness, for head bob
   "accents":[seconds...]}                                  # emphasis peaks, for brows / nods

Mouth letters (same as Rhubarb): X rest/closed, A closed lips (M B P), B slightly open teeth
(consonants, EE), C open (EH), D wide open (AH), E rounded (OH), F pucker (OO W), G teeth on lip
(F V), H tongue up (L).

HONESTY: the built-in estimator maps loudness and spectral balance to shapes. It is good enough
for stylised characters and fast speech, and it never claims phoneme accuracy; M/B/P and F/V
cannot be told apart from audio energy alone. For true phoneme shapes run Rhubarb Lip Sync
(github.com/DanielSWolf/rhubarb-lip-sync, MIT) on the voice file and pass its JSON with --rhubarb.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

SR = 16000


def load_mono(path: Path) -> np.ndarray:
    """Decode any audio/video file to mono 16 kHz float32 through ffmpeg."""
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "wav", str(wav)], check=True)
        from scipy.io import wavfile
        sr, x = wavfile.read(str(wav))
    x = x.astype(np.float32)
    if x.dtype.kind == "i" or np.abs(x).max() > 1.5:
        x = x / 32768.0
    return x


def smooth(a: np.ndarray, n: int) -> np.ndarray:
    if n <= 1:
        return a
    k = np.ones(n) / n
    return np.convolve(np.pad(a, (n // 2, n - 1 - n // 2), mode="edge"), k, mode="valid")


def features(x: np.ndarray, fps: int):
    hop = SR // fps
    win = int(SR * 0.032)
    n = max(1, (len(x) - win) // hop + 1)
    rms = np.zeros(n)
    cen = np.zeros(n)
    low = np.zeros(n)
    w = np.hanning(win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    for i in range(n):
        seg = x[i * hop : i * hop + win]
        if len(seg) < win:
            seg = np.pad(seg, (0, win - len(seg)))
        rms[i] = np.sqrt(np.mean(seg**2) + 1e-12)
        sp = np.abs(np.fft.rfft(seg * w))
        tot = sp.sum() + 1e-9
        cen[i] = (freqs * sp).sum() / tot
        low[i] = sp[(freqs >= 150) & (freqs < 1000)].sum() / tot
    return rms, cen, low


def estimate(x: np.ndarray, fps: int, words: list[dict] | None):
    rms, cen, low = features(x, fps)
    db = 20 * np.log10(rms + 1e-9)
    floor = np.percentile(db, 10)
    top = np.percentile(db, 97)
    span = max(12.0, top - floor)
    loud = np.clip((db - (floor + 0.18 * span)) / (0.82 * span), 0, 1)
    env = smooth(loud, 3)
    voiced = env > 0.08
    # close the mouth in real word gaps (from a transcript) when provided
    if words:
        gap = np.ones(len(env), bool)
        for w in words:
            a = int(float(w.get("start", w.get("t0", 0))) * fps)
            b = int(float(w.get("end", w.get("t1", 0))) * fps) + 1
            gap[max(0, a) : min(len(env), b)] = False
        voiced &= ~gap | (env > 0.35)
    shapes = np.array(["X"] * len(env), dtype="<U1")
    cmed = np.median(cen[voiced]) if voiced.any() else 1500.0
    for i in np.where(voiced)[0]:
        e, c, l = env[i], cen[i], low[i]
        if c > cmed * 1.55 and e < 0.55:
            shapes[i] = "B"  # hissy consonant / EE: teeth, slightly open
        elif l > 0.45 and e > 0.55:
            shapes[i] = "D"  # loud low-formant vowel: AH
        elif l > 0.38 and e > 0.30:
            shapes[i] = "E"  # rounded OH
        elif e > 0.30:
            shapes[i] = "C"  # open EH
        else:
            shapes[i] = "B"
    # lips close briefly at voiced -> quiet -> voiced dips (a B/M/P stand-in)
    for i in range(1, len(env) - 1):
        if voiced[i - 1] and voiced[i + 1] and env[i] < 0.5 * min(env[i - 1], env[i + 1]) and shapes[i] != "X":
            shapes[i] = "A"
    # remove one-frame flicker: a shape must hold >= 2 frames
    for i in range(1, len(shapes) - 1):
        if shapes[i] != shapes[i - 1] and shapes[i] != shapes[i + 1]:
            shapes[i] = shapes[i - 1]
    # accents = loudness peaks well above the local mean, >= 0.45 s apart
    accents: list[float] = []
    local = smooth(env, fps)
    for i in range(2, len(env) - 2):
        if env[i] > 0.7 and env[i] >= env[i - 1] and env[i] > env[i + 1] and env[i] > local[i] * 1.35:
            t = i / fps
            if not accents or t - accents[-1] >= 0.45:
                accents.append(round(t, 3))
    return shapes, env, accents


def to_cues(shapes: np.ndarray, fps: int):
    cues = []
    s = 0
    for i in range(1, len(shapes) + 1):
        if i == len(shapes) or shapes[i] != shapes[s]:
            cues.append({"t0": round(s / fps, 3), "t1": round(i / fps, 3), "v": str(shapes[s])})
            s = i
    return cues


def from_rhubarb(path: Path, dur: float | None):
    data = json.loads(path.read_text(encoding="utf-8"))
    cues = [{"t0": round(float(c["start"]), 3), "t1": round(float(c["end"]), 3), "v": c["value"]} for c in data["mouthCues"]]
    return cues, float(data.get("metadata", {}).get("duration", dur or (cues[-1]["t1"] if cues else 0)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio")
    ap.add_argument("--rhubarb")
    ap.add_argument("--words", help="JSON list of {start,end} word times (transcript) to close the mouth between words")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.audio and not a.rhubarb:
        ap.error("give --audio or --rhubarb")
    fps = a.fps
    env = np.zeros(0)
    accents: list[float] = []
    dur = 0.0
    if a.audio:
        x = load_mono(Path(a.audio))
        dur = len(x) / SR
    if a.rhubarb:
        cues, dur2 = from_rhubarb(Path(a.rhubarb), dur)
        dur = dur or dur2
        source = "rhubarb"
        if a.audio:
            _, env, accents = estimate(x, fps, None)
    else:
        words = None
        if a.words:
            raw = json.loads(Path(a.words).read_text(encoding="utf-8"))
            words = raw.get("words", raw) if isinstance(raw, dict) else raw
        shapes, env, accents = estimate(x, fps, words)
        cues = to_cues(shapes, fps)
        source = "estimate"
    out = {"fps": fps, "duration": round(dur, 3), "source": source, "cues": cues,
           "env": [round(float(v), 3) for v in env], "accents": accents}
    Path(a.out).write_text(json.dumps(out), encoding="utf-8")
    counts: dict[str, int] = {}
    for c in cues:
        counts[c["v"]] = counts.get(c["v"], 0) + 1
    print(f"viseme_track: {source}, {dur:.1f}s, {len(cues)} cues {counts}, {len(accents)} accents -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

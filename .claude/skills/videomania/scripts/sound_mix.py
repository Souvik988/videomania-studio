"""Phrased sound mix: voice + chapter-phrased music + loud, placed SFX, measured against the reference.

    python sound_mix.py <project_dir> --shots shots.js --voice input/vo.mp3 \
        --music audio/music/a.mp3:0-6.45,10.02-57.42 --music audio/music/b.mp3:63.22-80.48,83.1-113.55 \
        [--music-db -26] [--sfx-db -3] [--gap-db 4] [--duck-db 6] [--lufs -14]

Why this exists (lesson from the director film, 2026-11-14): a constant pumping music bed with hard ducking
and quiet SFX makes the film sound like "voice only". The reference reel breathes: music comes in by
chapter, stops for the dramatic beats, and every picture event has a sound you can hear on a phone.

What it does
1. Cues from the shot list (sfx_from_shots.build) plus extras the v2 kit can show: the opening flicker
   burst (glitch ticks), washes (glitch), pixel dissolves (sparkle). Caps as in crew job 7.
2. Places SFX: everything +sfx-db, and a cue that lands in a speech gap gets +3 dB more (it has the room).
3. Music is phrased: each --music file plays only inside its listed spans, continuing where it left off,
   with 0.25 s fades in and 0.6 s fades out. Gaps between spans are real silence (the drops).
4. Gentle ducking: up to --duck-db under the voice (30 ms attack, 350 ms release) — never 7:1 pumping.
5. Two-pass loudnorm to --lufs (TP -1.5), writes audio/master.wav and source/mix.wav.
6. Measures the momentary-loudness spread (ebur128 M, 400 ms): p10 / p50 / p90.
   Reference reel: -22.1 / -14.4 / -11.7 LUFS (floor-to-median -7.7, top +2.7).
   v1 (constant bed, quiet SFX): -19.6 / -15.0 / -12.2 (floor -4.6: the bed filled every gap).
   v2 with the defaults below: -21.1 / -14.9 / -11.5, SFX hits level with the voice (0 dB), music 20 dB under it.
   A bare voiceover alone reads about -9 floor: the pauses are in the voice; do not fill them.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brain  # noqa: E402
import sfx_from_shots  # noqa: E402

spec = importlib.util.spec_from_file_location("sfx_design", HERE / "sfx_design.py")
sfx = importlib.util.module_from_spec(spec); spec.loader.exec_module(sfx)
SR = sfx.SR


def load(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).astype(np.float64)


def write(path: Path, x: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def db(x: float) -> float:
    return 20 * np.log10(max(x, 1e-9))


def extra_cues(S: dict) -> list[dict]:
    out = []
    add = lambda t, n, why, g: out.append({"t": round(t, 3), "name": n, "gain_db": g, "pan": 0.0, "reason": why})
    for s in S["shots"]:
        f = s.get("flicker")
        if f:
            a, b = f["t"]; n = len(f.get("looks") or []) or 4
            for k in range(n):
                add(a + (b - a) * k / n, "glitch" if k % 2 == 0 else "tap_hi", f"flicker burst {k + 1}/{n}", -12)
        for w in s.get("wash") or []:
            add(w["t"], "glitch", f"wash {w.get('color', '')}", -11)
        for d in s.get("doodles") or []:   # the marker squeaks as it draws
            add(d["t"], "paper", f"doodle {d.get('kind', 'circle')}", -10)
        for c in s.get("cast") or []:
            for t in c.get("dissolve") or []:
                add(t, "sparkle", f"{c.get('who')} pixel dissolve", -12)
    return out


def speech_mask(words: list[dict], n: int, pad: float = 0.05) -> np.ndarray:
    m = np.zeros(n, bool)
    for w in words:
        m[int(max(0, w["start"] - pad) * SR):int((w["end"] + pad) * SR)] = True
    return m


def envelope_follow(x: np.ndarray, att: float, rel: float) -> np.ndarray:
    a, r = np.exp(-1 / (att * SR)), np.exp(-1 / (rel * SR))
    # block-wise (10 ms) for speed, then upsample
    hop = SR // 100
    blocks = np.sqrt(np.mean(np.square(x[: len(x) // hop * hop]).reshape(-1, hop), axis=1))
    a, r = a ** hop, r ** hop
    env = np.zeros_like(blocks); e = 0.0
    for i, v in enumerate(blocks):
        e = a * e + (1 - a) * v if v > e else r * e + (1 - r) * v
        env[i] = e
    up = np.repeat(env, hop) if len(env) else np.zeros(0)
    return np.pad(up, (0, max(0, len(x) - len(up))), mode="edge" if len(up) else "constant")[: len(x)]


def music_track(path: Path, spans: list[tuple[float, float]], n: int) -> np.ndarray:
    src = load(path)
    out = np.zeros((n, 2)); pos = 0
    for t0, t1 in spans:
        s, e = int(t0 * SR), min(n, int(t1 * SR)); L = e - s
        seg = np.take(src, np.arange(pos, pos + L) % len(src), axis=0)   # loops if the file runs out
        fi, fo = min(L, int(0.25 * SR)), min(L, int(0.6 * SR))
        g = np.ones(L); g[:fi] = np.linspace(0, 1, fi); g[L - fo:] *= np.linspace(1, 0, fo)
        out[s:e] += seg * g[:, None]; pos += L
    return out


def parse_cue(spec: str) -> dict:
    """file@offset:t0-t1[:gain=-3][:lp=1200][:in=0.03][:out=0.6] - one entrance of one song (see audio-cinematography.md)."""
    parts = spec.split(":")
    # a Windows drive letter is not a field
    if len(parts[0]) == 1 and parts[0].isalpha():
        parts = [parts[0] + ":" + parts[1]] + parts[2:]
    f, off = (parts[0].rsplit("@", 1) + ["0"])[:2]
    t0, t1 = (float(v) for v in parts[1].split("-"))
    c = {"file": f, "offset": float(off), "t0": t0, "t1": t1, "gain": 0.0, "lp": 0.0, "in": 0.04, "out": 0.6}
    for kv in parts[2:]:
        k, v = kv.split("="); c[k] = float(v)
    return c


def lowpass(x: np.ndarray, fc: float) -> np.ndarray:
    from scipy.signal import butter, sosfilt
    return sosfilt(butter(4, fc, btype="low", fs=SR, output="sos"), x, axis=0)


def ambience(n_s: int, seed: int = 3) -> np.ndarray:
    """Outdoor bed for real-world shots: soft wind (filtered noise, slow swell) and a few bird chirps."""
    rng = np.random.default_rng(seed); t = np.arange(n_s) / SR
    wind = lowpass(rng.standard_normal((n_s, 2)), 500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.18 * t + np.array([[0, 1.3]]).T).T) * 0.5
    birds = np.zeros(n_s)
    for k in range(int(len(t) / SR * 2.2)):
        s0 = int(rng.uniform(0, max(1, n_s - SR * 0.3))); L = int(SR * rng.uniform(0.06, 0.14)); tt = np.arange(L) / SR
        f0 = rng.uniform(2800, 4800); f = f0 + 1600 * np.sin(np.pi * tt / tt[-1]) * rng.choice([-1, 1])
        birds[s0:s0 + L] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / tt[-1]) ** 2 * rng.uniform(0.15, 0.4)
    out = wind + np.stack([birds * 0.8, birds], 1)
    return out / (np.sqrt(np.mean(out ** 2)) + 1e-9) * 0.05


def momentary(path: Path) -> tuple[float, float, float]:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    M = [float(l.split("M:")[1].split()[0]) for l in r.splitlines() if " M:" in l and "TARGET" in l]
    M = np.array([m for m in M if m > -70])
    return float(np.percentile(M, 10)), float(np.percentile(M, 50)), float(np.percentile(M, 90))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project"); ap.add_argument("--shots", required=True); ap.add_argument("--voice", required=True)
    ap.add_argument("--words", default="transcript/words.json")
    ap.add_argument("--music", action="append", default=[], help="file:t0-t1,t0-t1 (spans in film seconds)")
    ap.add_argument("--music-db", type=float, default=-26.0, help="music level relative to its own peak-normalised file")
    ap.add_argument("--sfx-db", type=float, default=-3.0); ap.add_argument("--gap-db", type=float, default=4.0)
    ap.add_argument("--duck-db", type=float, default=6.0); ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--cue", action="append", default=[], help="file@offset:t0-t1[:gain=dB][:lp=Hz][:in=s][:out=s] one song entrance; songs are level-matched by loudness")
    ap.add_argument("--dip", action="append", default=[], help="t0-t1:dB  music automation (e.g. drop the music on 'lower that voice')")
    ap.add_argument("--amb", action="append", default=[], help="t0-t1[:dB] outdoor ambience (wind, birds) for real-world shots")
    a = ap.parse_args()
    P = Path(a.project)
    S = brain.load_shots(str(P / a.shots))
    voice = load(P / a.voice)
    dur = float(S.get("duration") or S["shots"][-1]["t1"]); n = max(len(voice), int(dur * SR))
    voice = np.pad(voice, ((0, n - len(voice)), (0, 0)))
    words = json.loads((P / a.words).read_text(encoding="utf-8"))["words"]
    talk = speech_mask(words, n)

    # 1-2 SFX
    cues = sfx_from_shots.cap(sfx_from_shots.build(S) + extra_cues(S), dur)
    stem = np.zeros((n, 2)); cache = {}; in_gap = 0
    for c in cues:
        x = cache.setdefault(c["name"], sfx.LIB[c["name"]]())
        s = int(c["t"] * SR); e = min(n, s + len(x))
        if s >= n:
            continue
        gap = not talk[s:min(n, s + int(0.2 * SR))].any()
        in_gap += gap
        g = 10 ** ((c.get("gain_db", -10) + a.sfx_db + (a.gap_db if gap else 0)) / 20)
        p = float(c.get("pan", 0)); l, r = np.sqrt((1 - p) / 2) * 1.414, np.sqrt((1 + p) / 2) * 1.414
        stem[s:e, 0] += x[:e - s] * g * l; stem[s:e, 1] += x[:e - s] * g * r
    stem = np.tanh(stem)
    (P / "storyboard").mkdir(exist_ok=True)
    (P / "storyboard" / "sfx_cues.json").write_text(json.dumps({"duration": dur, "cues": cues}, indent=1, ensure_ascii=False), encoding="utf-8")

    # 3-4 music, phrased and gently ducked
    bed = np.zeros((n, 2))
    for m in a.music:
        f, spans = m.rsplit(":", 1)
        sp = [tuple(float(v) for v in x.split("-")) for x in spans.split(",")]
        tr = music_track(P / f, sp, n); pk = np.max(np.abs(tr)) or 1
        bed += tr / pk
    for spec in a.cue:
        c = parse_cue(spec); src = load(P / c["file"])
        s0, e0 = int(c["t0"] * SR), min(n, int(c["t1"] * SR)); L = e0 - s0
        seg = np.take(src, np.arange(int(c["offset"] * SR), int(c["offset"] * SR) + L) % len(src), axis=0)
        seg = seg / (np.sqrt(np.mean(seg ** 2)) + 1e-9) * 0.25           # every song at the same loudness
        if c["lp"]:
            seg = lowpass(seg, c["lp"])                                    # source music: from a speaker in the scene
        fi, fo = min(L, int(c["in"] * SR)), min(L, int(c["out"] * SR))
        g = np.ones(L); g[:fi] = np.linspace(0, 1, fi); g[L - fo:] *= np.linspace(1, 0, fo)
        bed[s0:e0] += seg * (g * 10 ** (c["gain"] / 20))[:, None]
    bed *= 10 ** (a.music_db / 20)
    for d in a.dip:
        span, dbv = d.split(":"); t0, t1 = (float(v) for v in span.split("-"))
        s0, e0 = int(t0 * SR), min(n, int(t1 * SR)); r = int(0.05 * SR)
        g = np.full(e0 - s0, 10 ** (float(dbv) / 20)); g[:r] = np.linspace(1, g[0], r); g[-r:] = np.linspace(g[0], 1, r)
        bed[s0:e0] *= g[:, None]
    for am in a.amb:
        span, *dbv = am.split(":"); t0, t1 = (float(v) for v in span.split("-"))
        s0, e0 = int(t0 * SR), min(n, int(t1 * SR)); x = ambience(e0 - s0) * 10 ** ((float(dbv[0]) if dbv else 0) / 20)
        fo = min(len(x), int(0.4 * SR)); x[-fo:] *= np.linspace(1, 0, fo)[:, None]
        stem[s0:e0] += x
    venv = envelope_follow(voice.mean(1), 0.03, 0.35)
    thr = np.percentile(venv[talk], 20) if talk.any() else 0.01
    duck = 10 ** (-a.duck_db * np.clip(venv / (thr * 2), 0, 1) / 20)
    bed *= duck[:, None]

    mix = voice + bed + stem
    pre = P / "audio" / "mix_pre.wav"; write(pre, mix / max(1.0, np.max(np.abs(mix)) / 0.98))
    write(P / "audio" / "stems" / "sfx_custom.wav", stem); write(P / "audio" / "stems" / "music_bed.wav", bed)

    # 5 loudnorm two-pass
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    lf = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    master = P / "audio" / "master.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", lf, "-ar", str(SR), str(master)], check=True)
    if (P / "source").exists():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(master), str(P / "source" / "mix.wav")], check=True)

    # 6 measure
    p10, p50, p90 = momentary(master)
    vs = np.sqrt(np.mean(np.square(voice[talk]))) if talk.any() else 1e-9
    nz = np.abs(stem).max(1) > 1e-3
    ss = np.sqrt(np.mean(np.square(stem[nz]))) if nz.any() else 1e-9
    bs = np.sqrt(np.mean(np.square(bed[talk]))) if talk.any() else 1e-9
    print(f"cues {len(cues)} ({in_gap} in speech gaps); SFX vs voice {db(ss) - db(vs):+.1f} dB; music under voice {db(bs) - db(vs):+.1f} dB")
    print(f"momentary p10 {p10:.1f} / p50 {p50:.1f} / p90 {p90:.1f} LUFS -> floor-to-median {p10 - p50:+.1f} dB (reference -7.7; p10/p50/p90 -22.1/-14.4/-11.7)")
    print("master:", master)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

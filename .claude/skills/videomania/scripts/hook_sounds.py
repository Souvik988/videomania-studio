"""Original hook sounds (synthesised, seeded, rights-clean): the ominous layer the CC0 kit does not have.

    python hook_sounds.py [-o <skill>/assets/sfx-hook/synth]

Writes 48 kHz WAV files + their sync points into manifest_synth.json:
  braam        the trailer "BRAAAM": detuned low brass-like saw stack, filter opening, saturation, hall tail (2.8 s)
  braam_short  a tighter braam for mid-film pattern interrupts (1.4 s)
  ominous_swell a dark rising drone that ends on the cut (sync at its end, 1.6 s): put it BEFORE a reveal
  tear         a reality-tearing glitch: noise ripped down in pitch with bit-crush stutter (0.6 s)
  sub_hit      a felt-more-than-heard sub thump with a click on top (1.2 s)
  heartbeat    two low thumps, lub-dub (0.9 s)
  tape_stop    the whole world slowing to a stop: a pitched tone falling to nothing (0.7 s)
  shutter_stutter  a rapid digital shutter burst (0.35 s), for freeze frames and stutters

Why: the user's reference reel opens on a "universe distorted" glitch with an ominous sound in the first second,
and that is what held viewers (their own reel lost 65 % in the first seconds without it).
"""
import argparse
import json
import wave
from pathlib import Path

import numpy as np

SR = 48000


def t_(d):
    return np.arange(int(d * SR)) / SR


def lp(x, fc):
    """one-pole low-pass with a per-sample cutoff array or scalar"""
    fc = np.broadcast_to(np.asarray(fc, dtype=float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s = (1 - a[i]) * x[i] + a[i] * s
        y[i] = s
    return y


def saw(f, t, phase=0.0):
    ph = np.cumsum(np.broadcast_to(f, t.shape) / SR) + phase
    return 2 * (ph - np.floor(ph + 0.5))


def hall(x, decay=1.6, seed=0):
    """cheap reverb: a decaying noise impulse response, convolved by FFT"""
    r = np.random.default_rng(seed)
    n = int(decay * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / (SR * decay / 5))
    ir[0] = 0
    y = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[: len(x) + n]
    return y / (np.max(np.abs(y)) + 1e-9)


def norm(x, peak=0.89):
    return x / (np.max(np.abs(x)) + 1e-9) * peak


def braam(d=2.8, f0=55.0, seed=1):
    t = t_(d)
    r = np.random.default_rng(seed)
    x = np.zeros_like(t)
    for k, mult in enumerate([1, 1, 2, 2, 3, 0.5]):
        det = 1 + r.uniform(-0.006, 0.006)
        x += saw(f0 * mult * det, t, r.random()) * (1.0 if mult <= 1 else 0.55 / mult)
    env = np.minimum(1, t / 0.035) * np.exp(-np.maximum(0, t - 0.25) / 1.1)
    cutoff = 180 + 2600 * np.exp(-t / 0.5) + 300 * np.minimum(1, t / 0.08)
    y = lp(x * env, cutoff)
    y = np.tanh(2.6 * y)                       # brass-like saturation
    y = 0.75 * y + 0.35 * hall(y, 2.2, seed)[: len(y)]
    return norm(y)


def ominous_swell(d=1.6, seed=2):
    t = t_(d)
    r = np.random.default_rng(seed)
    x = sum(saw(f * (1 + r.uniform(-0.01, 0.01)), t, r.random()) for f in (41.2, 61.7, 82.4, 98.0))
    noise = r.standard_normal(len(t)) * 0.4
    env = (t / d) ** 2.2
    y = lp((x + noise) * env, 120 + 3800 * (t / d) ** 2)
    y = np.tanh(1.8 * y)
    y[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))   # sudden stop on the cut
    return norm(y)


def tear(d=0.6, seed=3):
    t = t_(d)
    r = np.random.default_rng(seed)
    n = r.standard_normal(len(t))
    f = 4000 * np.exp(-t / 0.12) + 90
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.6
    y = lp(n, f * 1.5) + tone
    hold = np.repeat(y[::90], 90)[: len(y)]      # sample-and-hold crush
    gate = (np.floor(t * 38) % 2 == 0).astype(float) * 0.7 + 0.3
    y = (0.5 * y + 0.5 * hold) * gate * np.exp(-t / 0.22) * np.minimum(1, t / 0.003)
    return norm(y)


def sub_hit(d=1.2, seed=4):
    t = t_(d)
    f = 30 + 70 * np.exp(-t / 0.06)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45) * np.minimum(1, t / 0.002)
    click = np.random.default_rng(seed).standard_normal(len(t)) * np.exp(-t / 0.004) * 0.5
    return norm(np.tanh(1.5 * (y + click)))


def heartbeat(seed=5):
    one = sub_hit(0.45, seed)
    out = np.zeros(int(0.9 * SR))
    out[: len(one)] += one
    s = int(0.28 * SR)
    out[s: s + len(one)] += 0.75 * one[: len(out) - s]
    return norm(out)


def tape_stop(d=0.7, seed=6):
    t = t_(d)
    f = 220 * (1 - t / d) ** 2 + 8
    x = saw(f, t) + 0.5 * saw(f * 2.01, t)
    return norm(lp(x, 1200 * (1 - t / d) + 60) * np.minimum(1, t / 0.005) * (1 - t / d) ** 0.5)


def shutter_stutter(seed=7):
    r = np.random.default_rng(seed)
    out = np.zeros(int(0.35 * SR))
    for k in range(7):
        s = int(k * 0.045 * SR)
        n = r.standard_normal(int(0.012 * SR)) * np.exp(-np.arange(int(0.012 * SR)) / (0.003 * SR))
        out[s: s + len(n)] += n
    return norm(lp(out, 6000))


def write(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())


SOUNDS = {
    # id: (fn, sync_at seconds, tier, description, use_for)
    "braam": (braam, 0.03, "hard", "Trailer braam: a huge low brass-like blast with a long hall tail.", ["the first frame of a hook", "a reveal", "a dark turn"]),
    "braam_short": (lambda: braam(1.4, 65.4, 9), 0.03, "medium", "A tighter braam for a mid-film pattern interrupt.", ["chapter turn", "a hard statement"]),
    "ominous_swell": (ominous_swell, 1.59, "medium", "A dark drone rising to a sudden stop; its sync point is its END.", ["the 1-2 s before a reveal", "tension before a cut"]),
    "tear": (tear, 0.004, "hard", "Reality tearing: ripped noise, pitch falling, crushed stutter.", ["universe warp", "glitch hook", "world switch"]),
    "sub_hit": (sub_hit, 0.004, "hard", "A sub thump with a click: felt more than heard.", ["under any hit", "zoom punch", "the beat a word lands"]),
    "heartbeat": (heartbeat, 0.004, "medium", "Lub-dub: two low thumps.", ["suspense", "before a question is answered"]),
    "tape_stop": (tape_stop, 0.0, "medium", "The world winding down to a stop.", ["freeze frame", "record scratch moment", "a joke stop"]),
    "shutter_stutter": (shutter_stutter, 0.0, "soft", "Rapid digital shutter burst.", ["frame stutter", "freeze", "camera snap"]),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", default=str(Path(__file__).resolve().parent.parent / "assets" / "sfx-hook" / "synth"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    man = []
    for sid, (fn, sync, tier, desc, use) in SOUNDS.items():
        x = fn()
        p = out / f"{sid}.wav"
        write(p, x)
        man.append({"id": sid, "file": f"synth/{sid}.wav", "category": "hook-synth", "duration": round(len(x) / SR, 3),
                    "sync_at": sync, "tier": tier, "description": desc, "use_for": use,
                    "source": "Video Mania hook_sounds.py (original synthesis)", "license": "CC0-1.0"})
        print(f"{sid:16s} {len(x) / SR:5.2f}s")
    (out.parent / "manifest_synth.json").write_text(json.dumps(man, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()

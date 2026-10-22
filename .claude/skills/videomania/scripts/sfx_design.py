"""Original, rights-clean sound design (synthesised, seeded): UI taps, whooshes, booms, risers, glitch,
typing, message send, SMS/notification ding, cash-register ka-ching, coin burst, tick-tock, paper.
ROOT is the project folder (copy this file to projects/ID/tools/ or edit ROOT).

`python sfx.py lib`              → audio/sfx_lib/<name>.wav (audition set)
`python sfx.py stem cues.json`   → audio/stems/sfx_custom.wav from timed cues
Cue: {"t": 12.3, "name": "cash", "gain_db": -6, "pan": 0.0, "reason": "..."}
"""
import json, sys, wave
from pathlib import Path
import numpy as np

SR = 48000
ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def env(d, a=0.003, decay=0.2, curve=1.0):
    t = t_(d)
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(decay, 1e-4)) ** curve
    return e


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x); s = 0.0
    for i, v in enumerate(x):
        s = (1 - a) * v + a * s; y[i] = s
    return y


def bandnoise(d, f0, f1, q=1.5, seed=0):
    """Noise swept through a resonant band from f0 to f1 (state-variable filter)."""
    r = np.random.default_rng(seed)
    n = r.standard_normal(int(d * SR))
    f = np.geomspace(f0, f1, len(n))
    low = band = 0.0; out = np.empty_like(n)
    damp = 1.0 / q
    for i in range(len(n)):
        k = 2 * np.sin(np.pi * min(f[i], SR / 6) / SR)
        low += k * band
        high = n[i] - low - damp * band
        band += k * high
        out[i] = band
    return out / (np.abs(out).max() + 1e-9)


def bell(d, f, partials=((1, 1), (2.76, .5), (5.4, .3), (8.93, .15)), decay=0.6, seed=0):
    t = t_(d); y = np.zeros_like(t)
    for ratio, amp in partials:
        y += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * (1.2 + ratio * 0.9) / decay)
    return y * np.minimum(1, t / 0.002)


def norm(x, peak=0.9):
    return x / (np.abs(x).max() + 1e-9) * peak


# ---------------------------------------------------------------- sounds
def whoosh(d=0.6, up=True, seed=1):
    f0, f1 = (300, 4200) if up else (4200, 300)
    x = bandnoise(d, f0, f1, 1.1, seed)
    t = t_(d); e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return norm(x * e, 0.8)


def air(d=0.45, seed=2):
    x = bandnoise(d, 1800, 900, 0.7, seed)
    t = t_(d); e = np.sin(np.pi * t / d) ** 2
    return norm(x * e, 0.5)


def tap(f=1800, seed=3):
    d = 0.09; t = t_(d)
    body = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.012)
    click = bandnoise(d, 6000, 3000, 2, seed) * np.exp(-t / 0.004)
    return norm(body * 0.6 + click * 0.5, 0.7)


def click(seed=4):
    d = 0.05; t = t_(d)
    x = bandnoise(d, 5000, 2500, 3, seed) * np.exp(-t / 0.003)
    x += 0.4 * np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.006)
    return norm(x, 0.7)


def typing(n=10, gap=0.075, seed=5):
    r = np.random.default_rng(seed)
    out = np.zeros(int((n * gap + 0.2) * SR))
    for i in range(n):
        k = click(seed + i) * r.uniform(0.5, 1.0)
        s = int((i * gap + r.uniform(-0.015, 0.015)) * SR); s = max(s, 0)
        out[s:s + len(k)] += k[:len(out) - s]
    return norm(out, 0.6)


def send(seed=6):
    d = 0.22; t = t_(d)
    f = 600 + 900 * (t / d) ** 0.7
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 1.5
    return norm(y + 0.3 * air(d, seed), 0.6)


def ding(seed=7):
    """Two-note SMS/notification chime."""
    d1 = bell(0.9, 1567.98, decay=0.35); d2 = bell(1.2, 2093.0, decay=0.45)
    out = np.zeros(int(1.5 * SR)); out[:len(d1)] += d1
    s = int(0.11 * SR); out[s:s + len(d2)] += d2[:len(out) - s]
    return norm(out, 0.7)


def cash(seed=8):
    """Cash-register ka-ching: drawer slam + bright bell + tail."""
    r = np.random.default_rng(seed)
    out = np.zeros(int(1.8 * SR))
    # mechanical "ka": two clunks and a short rattle
    for k, at in ((0.9, 0.0), (0.7, 0.05)):
        d = 0.08; t = t_(d)
        thunk = bandnoise(d, 900, 300, 1.2, seed + int(at * 100)) * np.exp(-t / 0.02)
        thunk += 0.5 * np.sin(2 * np.pi * 140 * t) * np.exp(-t / 0.03)
        s = int(at * SR); out[s:s + len(thunk)] += k * thunk
    rat = bandnoise(0.12, 3000, 2000, 4, seed + 9) * (r.random(int(0.12 * SR)) > 0.85) * 0.6
    s = int(0.06 * SR); out[s:s + len(rat)] += rat
    # "ching": inharmonic bright bell
    b = bell(1.6, 2637.0, ((1, 1), (1.505, .6), (2.32, .45), (3.17, .3), (4.6, .2)), decay=0.55)
    b2 = bell(1.6, 3951.0, ((1, .6), (1.41, .3)), decay=0.4)
    s = int(0.13 * SR); out[s:s + len(b)] += 0.9 * b[:len(out) - s] + 0.4 * b2[:len(out) - s]
    return norm(out, 0.85)


def coins(n=26, d=1.1, seed=9):
    r = np.random.default_rng(seed)
    out = np.zeros(int((d + 0.5) * SR))
    times = np.sort(r.beta(1.3, 2.6, n) * d)
    for i, at in enumerate(times):
        f = r.uniform(3200, 6400)
        h = bell(0.25, f, ((1, 1), (1.37, .5), (2.11, .3)), decay=0.06 + r.uniform(0, .05))
        s = int(at * SR); out[s:s + len(h)] += h * r.uniform(0.3, 1.0) * (1 - 0.5 * at / d)
    return norm(out, 0.7)


def boom(seed=10):
    d = 1.6; t = t_(d)
    f = 55 * np.exp(-t * 0.6) + 32
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    hit = bandnoise(0.25, 2500, 200, 0.8, seed) * np.exp(-t_(0.25) / 0.05)
    out = sub.copy(); out[:len(hit)] += 0.55 * hit
    return norm(np.tanh(out * 1.6), 0.9)


def riser(d=1.4, seed=11):
    t = t_(d)
    x = bandnoise(d, 400, 7000, 1.4, seed) * (t / d) ** 2.2
    f = 220 * 2 ** (2.5 * t / d)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) ** 3 * 0.35
    return norm(x + tone, 0.7)


def glitch(seed=12):
    r = np.random.default_rng(seed)
    d = 0.45; n = int(d * SR); out = np.zeros(n); i = 0
    while i < n:
        L = int(r.uniform(0.012, 0.05) * SR)
        f = r.choice([180, 360, 1440, 2880, 90])
        seg = np.sign(np.sin(2 * np.pi * f * t_(L / SR))) * r.uniform(0.2, 0.8)
        if r.random() < 0.35:
            seg = r.standard_normal(L) * 0.5
        out[i:i + L] = seg[:n - i]; i += L + int(r.uniform(0, 0.02) * SR)
    q = 16; out = np.round(out * q) / q
    return norm(out * np.exp(-t_(d) / 0.3), 0.45)


def ticktock(n=4, gap=0.5, seed=13):
    out = np.zeros(int((n * gap + 0.3) * SR))
    for i in range(n):
        k = tap(2600 if i % 2 == 0 else 2000, seed + i)
        s = int(i * gap * SR); out[s:s + len(k)] += k
    return norm(out, 0.6)


def paper(seed=14):
    r = np.random.default_rng(seed)
    d = 0.5; t = t_(d)
    x = bandnoise(d, 2500, 4500, 0.6, seed) * (r.random(len(t)) > 0.6)
    x = x * np.sin(np.pi * t / d) ** 0.8
    return norm(x, 0.45)


def error(seed=15):
    d = 0.32; t = t_(d)
    y = (np.sign(np.sin(2 * np.pi * 150 * t)) * 0.4 + np.sin(2 * np.pi * 300 * t)) * np.exp(-t / 0.15)
    y = onepole_lp(y, 1800)
    return norm(y, 0.45)


def shutter(seed=16):
    out = np.zeros(int(0.25 * SR))
    for at, k in ((0, 1), (0.07, 0.7)):
        c = click(seed + int(at * 100)); s = int(at * SR); out[s:s + len(c)] += k * c
    return norm(out, 0.6)


def sparkle(seed=17):
    r = np.random.default_rng(seed)
    out = np.zeros(int(1.2 * SR))
    for i in range(9):
        f = 1046.5 * 2 ** (r.integers(0, 12) / 12) * 2
        b = bell(0.6, f, ((1, 1), (2, .2)), decay=0.18)
        s = int(i * 0.07 * SR); out[s:s + len(b)] += b[:len(out) - s] * (0.4 + 0.6 * r.random())
    return norm(out, 0.5)


LIB = {
    "whoosh": lambda: whoosh(0.55, True, 1), "whoosh_long": lambda: whoosh(0.9, True, 21),
    "whoosh_down": lambda: whoosh(0.5, False, 22), "air": air, "tap": tap, "click": click,
    "typing": typing, "send": send, "ding": ding, "cash": cash, "coins": coins, "boom": boom,
    "riser": riser, "glitch": glitch, "ticktock": ticktock, "paper": paper, "error": error,
    "shutter": shutter, "sparkle": sparkle, "tap_hi": lambda: tap(2600, 31), "tap_lo": lambda: tap(1100, 32),
}


def write(path, x, stereo=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if stereo is None:
        stereo = np.stack([x, x], -1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def main():
    if sys.argv[1] == "lib":
        for k, fn in LIB.items():
            write(ROOT / "audio" / "sfx_lib" / f"{k}.wav", fn())
        print("lib", len(LIB))
        return
    cues = json.loads(Path(sys.argv[2]).read_text(encoding="utf8"))
    dur = float(cues["duration"])
    out = np.zeros((int(dur * SR), 2))
    cache = {}
    for c in cues["cues"]:
        x = cache.setdefault(c["name"], LIB[c["name"]]())
        g = 10 ** (c.get("gain_db", -10) / 20)
        p = float(c.get("pan", 0))
        l, r = np.sqrt((1 - p) / 2), np.sqrt((1 + p) / 2)
        s = int(c["t"] * SR); e = min(len(out), s + len(x))
        if s >= len(out):
            continue
        out[s:e, 0] += x[:e - s] * g * l * 1.414
        out[s:e, 1] += x[:e - s] * g * r * 1.414
    write(ROOT / "audio" / "stems" / "sfx_custom.wav", None, stereo=np.tanh(out))
    print("stem", len(cues["cues"]), "cues")


if __name__ == "__main__":
    main()

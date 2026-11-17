"""Editor effects pass: the CapCut / Premiere "inbuilt effects" layer, applied to ANY rendered film, each effect
paired with its sound. Deterministic (seeded per frame), frame-exact, works for every engine's output.

    python fx_pass.py list                                     # the 38 presets, by family, with their story job
    python fx_pass.py plan  <project> [--shots source/shots.js] [--video renders/x.mp4] [--hook warp|glitch|shock|flashzoom]
                                   -> <project>/storyboard/fx_cues.json  (an editor's plan you can edit)
    python fx_pass.py apply <in.mp4> <fx_cues.json> -o <out.mp4> [--lufs -14]
    python fx_pass.py gallery <in.mp4> --at 3.0 -o <dir>       # every preset on one frame -> contact sheet
    python fx_pass.py check <fx_cues.json>                      # the hook / density / photosensitivity gates

Why (user's note, 2026-11-15): their reel got 200 views and a 65 % skip rate; the reference (50K likes) opens with a
"universe distorted" glitch in the first second on an ominous sound, and keeps re-hooking with editor effects and hit
sounds. Video Mania never used those inbuilt-editor effects. This pass is that layer: a hook stack on frame 0, a
pattern interrupt at every chapter turn, a hit on punch words, an ending accent - every effect with its sound.

Cue: {"t": 0.0, "fx": "universe_warp", "dur": 0.7, "amount": 1.0,
      "sfx": [{"id": "braam", "at": "start", "gain_db": 0}], "why": "..."}
  t = the EVENT time (the first frame, the cut, the word). Presets marked `around` run [t - dur/2, t + dur/2].
  sfx `at`: start | peak | end - which moment of the effect the sound's sync point lands on.
Sounds come from <skill>/assets/sfx-hook (sfx_library.py find "..."); levels are matched from measured loudness.
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import cv2

SKILL = Path(__file__).resolve().parent.parent
LIB = SKILL / "assets" / "sfx-hook"
SR = 48000

# ----------------------------------------------------------------------------------------------- envelopes
ENV = {
    "hit": lambda u: (min(1.0, u / 0.08)) * (1 - u) ** 1.6,      # slam in, decay
    "swell": lambda u: math.sin(math.pi * u),                      # up and down (cuts: peak on the cut)
    "hold": lambda u: 1.0 if u < 0.92 else (1 - u) / 0.08,
    "rise": lambda u: u ** 2,
    "flick": lambda u: 1.0 if u < 0.5 else 0.0,
    "slam": lambda u: (1 - u) ** 1.4,                              # full strength on the FIRST frame (hooks)
}

# ----------------------------------------------------------------------------------------------- helpers
_grid = {}


def grid(h, w):
    if (h, w) not in _grid:
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        _grid[(h, w)] = (xs, ys)
    return _grid[(h, w)]


def remap(img, mx, my):
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def shift(img, dx, dy=0.0):
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, m, (img.shape[1], img.shape[0]), borderMode=cv2.BORDER_REFLECT)


def zoom(img, s, cx=0.5, cy=0.5, rot=0.0):
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w * cx, h * cy), rot, s)
    return cv2.warpAffine(img, m, (w, h), borderMode=cv2.BORDER_REFLECT)


def blend(a, b, k):
    return cv2.addWeighted(a, 1 - k, b, k, 0)


def radial_channels(img, k):
    """chromatic aberration: R scaled out, B scaled in"""
    r = zoom(img[:, :, 0], 1 + 0.012 * k)
    b = zoom(img[:, :, 2], 1 - 0.012 * k)
    return np.dstack([r, img[:, :, 1], b])


def vignette(img, k):
    h, w = img.shape[:2]
    xs, ys = grid(h, w)
    d = ((xs / w - 0.5) ** 2 + (ys / h - 0.5) ** 2) * 2.2
    m = np.clip(1 - k * d, 0, 1)[..., None]
    return (img * m).astype(np.uint8)


# ----------------------------------------------------------------------------------------------- effects
# each: fn(img, k, u, i, rng, ctx) -> img ; k = envelope * amount (0..1+), u = progress 0..1, i = frame index in cue
def fx_rgb_split(img, k, u, i, rng, ctx):
    d = img.shape[1] * 0.012 * k * (1 + rng.uniform(-0.4, 0.4))
    out = img.copy()
    out[:, :, 0] = shift(img[:, :, 0], d, rng.uniform(-2, 2) * k)
    out[:, :, 2] = shift(img[:, :, 2], -d, 0)
    return out


def fx_glitch_slices(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    out = img.copy()
    for _ in range(int(4 + 10 * k)):
        y0 = rng.integers(0, h - 4)
        bh = int(rng.integers(4, max(6, int(h * 0.09))))
        dx = int(rng.normal(0, w * 0.06 * k))
        out[y0:y0 + bh] = np.roll(img[y0:y0 + bh], dx, axis=1)
        if rng.random() < 0.35:
            out[y0:y0 + bh, :, 0] = np.roll(out[y0:y0 + bh, :, 0], int(w * 0.01 * k), axis=1)
    return out


def fx_block_corrupt(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    out = img.copy()
    for _ in range(int(3 + 14 * k)):
        bs = int(rng.choice([16, 32, 48, 64]) * (h / 1080))
        y, x = rng.integers(0, h - bs), rng.integers(0, w - bs)
        sy, sx = np.clip(y + rng.integers(-bs * 3, bs * 3), 0, h - bs), np.clip(x + rng.integers(-bs * 6, bs * 6), 0, w - bs)
        blk = img[sy:sy + bs, sx:sx + bs]
        out[y:y + bs, x:x + bs] = (blk // 48 * 48) if rng.random() < 0.5 else blk
    return out


def fx_digital_glitch(img, k, u, i, rng, ctx):
    out = fx_glitch_slices(img, k, u, i, rng, ctx)
    out = fx_rgb_split(out, k * 0.8, u, i, rng, ctx)
    if rng.random() < 0.5 * k:
        out = fx_block_corrupt(out, k, u, i, rng, ctx)
    prev = ctx.get("prev")
    if prev is not None and rng.random() < 0.25 * k:
        out = blend(out, prev, 0.5)
    return out


def fx_static_burst(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    n = rng.integers(0, 255, (h // 2, w // 2), dtype=np.uint8)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_NEAREST)
    n = np.dstack([n] * 3)
    n[::3] = n[::3] // 2
    return blend(img, n, min(0.85, 0.65 * k))


def fx_invert_flash(img, k, u, i, rng, ctx):
    return (255 - img) if (i % 4 < 2 and k > 0.3) else img


def fx_frame_stutter(img, k, u, i, rng, ctx):
    buf = ctx["buf"]
    if len(buf) > 3 and k > 0.2:
        held = buf[-1 - (i % 3)]
        return zoom(held, 1 + 0.02 * k)
    return img


def fx_signal_drop(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    out = shift(img, 0, rng.normal(0, h * 0.02 * k))
    out = cv2.cvtColor(cv2.cvtColor(out, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB) if rng.random() < 0.5 * k else out
    for _ in range(int(6 * k)):
        y = rng.integers(0, h - 6)
        out[y:y + rng.integers(2, 8)] = 0
    return out


def fx_universe_warp(img, k, u, i, rng, ctx):
    """THE hook: the world twists, bulges and splits its colours, then snaps back"""
    h, w = img.shape[:2]
    xs, ys = grid(h, w)
    cx, cy = w * 0.5, h * 0.5
    dx, dy = xs - cx, ys - cy
    r = np.sqrt(dx * dx + dy * dy)
    R = math.hypot(cx, cy)
    rn = r / R
    ang = k * 2.4 * (1 - rn) ** 2 * (1 if (i // 2) % 2 == 0 else 0.85)
    bulge = 1 - 0.28 * k * (1 - rn ** 2)
    ca, sa = np.cos(ang), np.sin(ang)
    mx = (cx + (dx * ca - dy * sa) * bulge).astype(np.float32)
    my = (cy + (dx * sa + dy * ca) * bulge).astype(np.float32)
    out = remap(img, mx, my)
    out = radial_channels(out, 2.5 * k)
    out = zoom(out, 1 + 0.12 * k)
    if k > 0.5 and rng.random() < 0.5:
        out = fx_glitch_slices(out, k * 0.6, u, i, rng, ctx)
    return vignette(out, 0.5 * k)


def fx_shockwave(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    xs, ys = grid(h, w)
    cx, cy = w * ctx.get("cx", 0.5), h * ctx.get("cy", 0.5)
    dx, dy = xs - cx, ys - cy
    r = np.sqrt(dx * dx + dy * dy) + 1e-3
    ring = u * math.hypot(w, h) * 0.75
    band = np.exp(-((r - ring) / (h * 0.06)) ** 2)
    amp = 28 * (h / 1080) * band * (1 - u) * min(1.0, ctx.get("amount", 1.0))
    mx = (xs - dx / r * amp).astype(np.float32)
    my = (ys - dy / r * amp).astype(np.float32)
    out = remap(img, mx, my)
    glow = (band * 60 * (1 - u))[..., None]
    return np.clip(out + glow, 0, 255).astype(np.uint8)


def fx_lens_bulge(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    xs, ys = grid(h, w)
    cx, cy = w / 2, h / 2
    dx, dy = (xs - cx) / cx, (ys - cy) / cy
    r2 = dx * dx + dy * dy
    s = 1 - 0.35 * k * np.clip(1 - r2, 0, 1)
    return remap(img, (cx + dx * s * cx).astype(np.float32), (cy + dy * s * cy).astype(np.float32))


def fx_wave_warp(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    xs, ys = grid(h, w)
    mx = (xs + w * 0.02 * k * np.sin(2 * np.pi * (ys / (h * 0.18) + u * 3))).astype(np.float32)
    return remap(img, mx, ys)


def fx_zoom_punch(img, k, u, i, rng, ctx):
    return zoom(img, 1 + 0.16 * k, ctx.get("cx", 0.5), ctx.get("cy", 0.5))


def fx_flash_zoom(img, k, u, i, rng, ctx):
    out = zoom(img, 1 + 0.22 * k)
    return fx_flash_white(out, 0.9 - 0.3 * i, u, i, rng, ctx) if i < 3 else fx_chromatic(out, k, u, i, rng, ctx)


def fx_zoom_blur(img, k, u, i, rng, ctx):
    acc = img.astype(np.float32)
    n = 6
    for j in range(1, n):
        acc += zoom(img, 1 + 0.025 * k * j)
    return (acc / n).astype(np.uint8)


def fx_shake(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    a = w * 0.014 * k
    return zoom(shift(img, rng.normal(0, a), rng.normal(0, a * 0.7)), 1 + 0.03 * k, rot=rng.normal(0, 0.6 * k))


def fx_whip_blur(img, k, u, i, rng, ctx):
    ln = max(1, int(img.shape[1] * 0.06 * k))
    ker = np.ones((1, ln), np.float32) / ln
    out = cv2.filter2D(img, -1, ker)
    return shift(out, img.shape[1] * 0.04 * k * ctx.get("dir", 1))


def fx_flash_white(img, k, u, i, rng, ctx):
    return blend(img, np.full_like(img, 255), min(1.0, k))


def fx_flash_color(img, k, u, i, rng, ctx):
    c = ctx.get("color", (225, 29, 46))
    return blend(img, np.full_like(img, c, dtype=np.uint8), min(0.9, k * 0.85))


def _blob(h, w, cx, cy, rx, ry):
    xs, ys = grid(h, w)
    return np.exp(-(((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2))


def fx_light_leak(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    b = _blob(h, w, w * (-0.2 + 1.4 * u), h * (0.3 + 0.2 * math.sin(u * 3)), w * 0.45, h * 0.7)
    col = np.array([255, 140, 60], np.float32)
    add = (b[..., None] * col * 0.75 * k)
    return np.clip(img.astype(np.float32) + add, 0, 255).astype(np.uint8)


def fx_film_burn(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    add = np.zeros((h, w), np.float32)
    r2 = np.random.default_rng(ctx.get("seed", 1))
    for j in range(4):
        cx, cy = r2.uniform(0, w), r2.uniform(0, h)
        add += _blob(h, w, cx + u * w * 0.3, cy, w * (0.15 + 0.3 * u), h * (0.2 + 0.4 * u))
    add = np.clip(add * k * 1.4, 0, 1.5)[..., None]
    col = np.array([255, 120, 30], np.float32)
    out = img.astype(np.float32) * (1 - 0.3 * np.clip(add, 0, 1)) + add * col
    return np.clip(out, 0, 255).astype(np.uint8)


def fx_flare_streak(img, k, u, i, rng, ctx):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, m = cv2.threshold(g, 200, 255, cv2.THRESH_BINARY)
    st = cv2.blur(m.astype(np.float32), (img.shape[1] // 3, 3))
    st = cv2.GaussianBlur(st, (0, 0), 6)
    col = np.array([120, 180, 255], np.float32)
    return np.clip(img + (st[..., None] / 255.0) * col * 1.6 * k, 0, 255).astype(np.uint8)


def fx_bloom_pulse(img, k, u, i, rng, ctx):
    b = cv2.GaussianBlur(img, (0, 0), img.shape[0] * 0.02)
    return cv2.addWeighted(img, 1.0, b, 0.8 * k, 0)


def fx_vhs(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    ycc = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb)
    ycc[:, :, 1] = shift(ycc[:, :, 1], w * 0.008 * k)
    ycc[:, :, 2] = shift(ycc[:, :, 2], -w * 0.006 * k)
    out = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2RGB)
    out = cv2.GaussianBlur(out, (3, 3), 0)
    y = int((u * 1.7 % 1) * h)
    band = slice(max(0, y - int(h * 0.03)), min(h, y + int(h * 0.03)))
    out[band] = np.roll(out[band], int(w * 0.03 * k), axis=1)
    out = np.clip(out.astype(np.int16) + rng.integers(-18, 18, out.shape[:2])[..., None] * k, 0, 255).astype(np.uint8)
    out[::2] = (out[::2] * (1 - 0.18 * k)).astype(np.uint8)
    return out


def fx_crt(img, k, u, i, rng, ctx):
    out = fx_lens_bulge(img, 0.25 * k, u, i, rng, ctx)
    out[::3] = (out[::3] * (1 - 0.35 * k)).astype(np.uint8)
    return vignette(out, 0.6 * k)


def fx_film_grain(img, k, u, i, rng, ctx):
    n = rng.normal(0, 14 * k, img.shape[:2]).astype(np.int16)[..., None]
    return np.clip(img.astype(np.int16) + n, 0, 255).astype(np.uint8)


def fx_old_film(img, k, u, i, rng, ctx):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    sep = np.dstack([g * 1.07, g * 0.92, g * 0.72])
    out = blend(img, np.clip(sep, 0, 255).astype(np.uint8), min(1, k))
    out = (out * (1 + rng.uniform(-0.08, 0.08) * k)).clip(0, 255).astype(np.uint8)
    h, w = out.shape[:2]
    for _ in range(int(2 * k)):
        x = rng.integers(0, w)
        out[:, x:x + 2] = 230
    return fx_film_grain(out, k * 0.8, u, i, rng, ctx)


def fx_bw_hit(img, k, u, i, rng, ctx):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.convertScaleAbs(g, alpha=1.35, beta=-30)
    return blend(img, cv2.cvtColor(g, cv2.COLOR_GRAY2RGB), min(1, k))


def fx_color_pop(img, k, u, i, rng, ctx):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + 0.7 * k), 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    return cv2.convertScaleAbs(out, alpha=1 + 0.12 * k, beta=-10 * k)


def fx_red_alert(img, k, u, i, rng, ctx):
    tint = img.astype(np.float32) * np.array([1.0, 0.45, 0.45])
    return blend(img, tint.astype(np.uint8), min(1, k * 0.8))


def fx_negative(img, k, u, i, rng, ctx):
    return blend(img, 255 - img, min(1, k))


def fx_echo_trails(img, k, u, i, rng, ctx):
    prev = ctx.get("prev_out")
    if prev is None:
        return img
    return np.maximum(img, (prev * (0.82 * k)).astype(np.uint8))


def fx_freeze_hold(img, k, u, i, rng, ctx):
    if "frozen" not in ctx:
        ctx["frozen"] = img.copy()
    f = zoom(ctx["frozen"], 1 + 0.06 * u)
    f = fx_bw_hit(f, 0.35, u, i, rng, ctx) if ctx.get("desat", True) else f
    return fx_flash_white(f, 0.6, u, i, rng, ctx) if i < 2 else f


def fx_pixelate(img, k, u, i, rng, ctx):
    h, w = img.shape[:2]
    bs = max(1, int(56 * k * (h / 1080)))
    if bs < 2:
        return img
    small = cv2.resize(img, (max(1, w // bs), max(1, h // bs)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)


def fx_chromatic(img, k, u, i, rng, ctx):
    return radial_channels(img, 3 * k)


# transitions across a cut (centre = around): peak on the cut
def fx_glitch_cut(img, k, u, i, rng, ctx):
    out = fx_digital_glitch(img, k, u, i, rng, ctx)
    return (255 - out) if abs(u - 0.5) < 0.04 else out


def fx_whip_cut(img, k, u, i, rng, ctx):
    ctx["dir"] = 1 if u < 0.5 else 1
    return fx_whip_blur(img, k * 1.4, u, i, rng, ctx)


def fx_zoom_cut(img, k, u, i, rng, ctx):
    out = fx_zoom_blur(img, k * 1.6, u, i, rng, ctx)
    return zoom(out, 1 + 0.25 * k) if u < 0.5 else zoom(out, 1 + 0.12 * k)


def fx_flash_cut(img, k, u, i, rng, ctx):
    return fx_flash_white(img, k * 0.95, u, i, rng, ctx)


def fx_pixel_cut(img, k, u, i, rng, ctx):
    return fx_pixelate(img, k, u, i, rng, ctx)


# ----------------------------------------------------------------------------------------------- catalogue
P = lambda fn, fam, env, dur, centre, job, avoid, sfx: dict(fn=fn, family=fam, env=env, dur=dur, centre=centre, job=job, avoid=avoid, sfx=sfx)
PRESETS = {
    # HOOK
    "universe_warp": P(fx_universe_warp, "hook", "slam", 0.75, "start", "Frame 0: the world twists, bulges and splits colour, then snaps into the film. The scroll-stopper.", "more than once per film",
                       [("braam", "start", 0), ("tear", "start", -4), ("bass-sub-drop-short", "start", -3)]),
    "shockwave": P(fx_shockwave, "hook", "hold", 0.6, "start", "A ring of force from the subject: a reveal, a 'boom' statement, a name.", "busy frames",
                   [("boom-drop-medium", "start", 0), ("sub_hit", "start", -3)]),
    "glitch_hook": P(fx_digital_glitch, "hook", "slam", 0.6, "start", "Frame 0 for tech / AI / hacking subjects: the signal breaks, then locks on.", "calm or warm films",
                     [("digital-corrupt", "start", 0), ("cinematic-drum-big", "start", -2), ("bass-sub-drop-short", "start", -4)]),
    "flash_zoom_hook": P(fx_flash_zoom, "hook", "slam", 0.5, "start", "Frame 0: white flash into a hard zoom punch: energetic, bright subjects.", "dark ominous openings",
                         [("cinematic-slam-big", "start", 0), ("whoosh-fast-hard", "start", -4)]),
    # GLITCH
    "rgb_split": P(fx_rgb_split, "glitch", "hit", 0.35, "start", "Colour channels tear apart for a beat: a light accent on a word or a turn.", "faces in close-up for long", [("digital-glitch-subtle", "start", 0)]),
    "glitch_slices": P(fx_glitch_slices, "glitch", "hit", 0.4, "start", "Horizontal bands jump sideways: 'wrong', 'error', 'myth'.", "warm emotional beats", [("digital-glitch-clear", "start", 0)]),
    "digital_glitch": P(fx_digital_glitch, "glitch", "swell", 0.5, "start", "Full digital break-up: slices, colour split, corrupt blocks.", "more than 3 per minute", [("digital-corrupt", "start", 0)]),
    "block_corrupt": P(fx_block_corrupt, "glitch", "hit", 0.4, "start", "Macroblocks smear and posterise: data, AI, broken files.", "", [("digital-scramble", "start", -2)]),
    "static_burst": P(fx_static_burst, "glitch", "hit", 0.3, "start", "TV snow over the picture: a channel change, a cut to a new world.", "", [("digital-static", "start", 0)]),
    "invert_flash": P(fx_invert_flash, "glitch", "hold", 0.2, "start", "Two-frame negative flicker: a shock word.", "photosensitive pacing: max 3 per second", [("sub_hit", "start", -2)]),
    "frame_stutter": P(fx_frame_stutter, "glitch", "hold", 0.45, "start", "The picture stammers on its last frames: a double-take, a 'wait...'.", "", [("shutter_stutter", "start", 0)]),
    "signal_drop": P(fx_signal_drop, "glitch", "hit", 0.5, "start", "Signal failing: black lines, jumps, colour loss: a lie, a crash, 'it failed'.", "", [("digital-signal-drop", "start", 0)]),
    # DISTORT
    "lens_bulge": P(fx_lens_bulge, "distort", "hit", 0.35, "start", "Fisheye punch toward the viewer: 'YOU', a direct address.", "", [("move-zoom-in", "peak", -2)]),
    "wave_warp": P(fx_wave_warp, "distort", "swell", 0.7, "start", "Heat-haze wobble: a dream, a memory, confusion.", "", [("whoosh-slow-hard", "peak", -6)]),
    "chromatic": P(fx_chromatic, "distort", "hit", 0.4, "start", "Radial colour fringing: lens stress on an impact.", "", [("impact-deep-hard", "start", -3)]),
    # CAMERA
    "zoom_punch": P(fx_zoom_punch, "camera", "hit", 0.35, "start", "Snap zoom-in on the punch word, then settle: the classic emphasis.", "every word: max one per chapter", [("sub_hit", "start", -2), ("whoosh-fast-medium", "start", -8)]),
    "zoom_blur": P(fx_zoom_blur, "camera", "hit", 0.35, "start", "Radial speed blur: 'fast', 'instantly', travel.", "", [("whoosh-fast-hard", "start", -2)]),
    "shake": P(fx_shake, "camera", "hit", 0.45, "start", "Impact shake: something lands, a big claim, a slam.", "dialogue-heavy holds", [("cinematic-slam-big", "start", 0)]),
    "whip_blur": P(fx_whip_blur, "camera", "swell", 0.3, "start", "Sideways whip: moving on, 'next'.", "", [("whoosh-fast-hard", "peak", 0)]),
    # LIGHT
    "flash_white": P(fx_flash_white, "light", "hit", 0.25, "start", "A white flash: a reveal, a new world, a camera snap.", "max 3 flashes per second", [("cinematic-drum-big", "start", -2)]),
    "flash_color": P(fx_flash_color, "light", "hit", 0.25, "start", "A flash in the brand red: an alarm word.", "", [("boom-hit-medium", "start", -2)]),
    "light_leak": P(fx_light_leak, "light", "swell", 1.2, "start", "Warm light sweeping across: nostalgia, a win, the ending.", "tense moments", [("whoosh-slow-hard", "peak", -8), ("shimmer-short-soft", "peak", -8)]),
    "film_burn": P(fx_film_burn, "light", "swell", 0.9, "start", "Orange film burn eating the frame: a chapter ending, a memory closing.", "", [("whoosh-slow-hard", "peak", -6)]),
    "flare_streak": P(fx_flare_streak, "light", "swell", 0.8, "start", "Anamorphic streak from the brights: premium, cinematic, a product hero.", "dark frames (no brights)", [("shimmer-short-soft", "peak", -6)]),
    "bloom_pulse": P(fx_bloom_pulse, "light", "hit", 0.4, "start", "The whole frame glows for a beat: 'magic', 'perfect', a win.", "", [("sting-bright-short", "start", -8)]),
    # TEXTURE / RETRO
    "vhs": P(fx_vhs, "texture", "hold", 1.0, "start", "VHS tape: the past, 'back then', a flashback.", "the whole film", [("digital-static", "start", -8)]),
    "crt": P(fx_crt, "texture", "hold", 1.0, "start", "Old monitor scanlines: inside a screen, retro tech.", "", [("digital-power-up", "start", -6)]),
    "film_grain": P(fx_film_grain, "texture", "hold", 1.5, "start", "Grain texture: a documentary, 'real' footage beat.", "", []),
    "old_film": P(fx_old_film, "texture", "hold", 1.5, "start", "Sepia, scratches, flicker: history, 'years ago'.", "", []),
    # COLOR
    "bw_hit": P(fx_bw_hit, "color", "hold", 0.6, "start", "Drop to black and white: 'stop', a sober truth, the problem.", "", [("sub_hit", "start", -4)]),
    "color_pop": P(fx_color_pop, "color", "hit", 0.6, "start", "Saturation surge: the answer, colour returning after bw_hit.", "", [("shimmer-short-soft", "start", -6)]),
    "red_alert": P(fx_red_alert, "color", "hold", 0.6, "start", "Red tint: danger, wrong, warning.", "", [("digital-denied", "start", -4)]),
    "negative": P(fx_negative, "color", "hold", 0.3, "start", "Full negative: an upside-down idea.", "", [("tear", "start", -6)]),
    # TIME
    "echo_trails": P(fx_echo_trails, "time", "hold", 0.8, "start", "Motion trails: speed, a blur of work, 'everything at once'.", "static shots (no effect)", [("whoosh-medium-hard", "start", -6)]),
    "freeze_hold": P(fx_freeze_hold, "time", "hold", 0.8, "start", "Freeze frame with a push: 'this is me', a record-scratch moment.", "", [("tape_stop", "start", -2), ("shutter_stutter", "start", -6)]),
    "pixelate": P(fx_pixelate, "time", "swell", 0.4, "start", "Pixel break-up and resolve: entering a game / pixel world.", "", [("digital-glitch-clear", "peak", -2)]),
    # TRANSITIONS (around the cut)
    "glitch_cut": P(fx_glitch_cut, "transition", "swell", 0.36, "around", "A glitch across the cut: the default energetic cut.", "", [("digital-glitch-clear", "peak", 0), ("whoosh-fast-hard", "peak", -6)]),
    "whip_cut": P(fx_whip_cut, "transition", "swell", 0.3, "around", "Whip pan across the cut.", "", [("whoosh-fast-hard", "peak", 0)]),
    "zoom_cut": P(fx_zoom_cut, "transition", "swell", 0.4, "around", "Zoom through into the next shot.", "", [("move-zoom-in", "peak", -2), ("boom-hit-soft", "peak", -6)]),
    "flash_cut": P(fx_flash_cut, "transition", "swell", 0.24, "around", "White flash across the cut: a new world.", "max 3 flashes per second", [("cinematic-drum-big", "peak", -4)]),
    "pixel_cut": P(fx_pixel_cut, "transition", "swell", 0.4, "around", "Pixelate out and back in: pixel worlds.", "", [("digital-glitch-subtle", "peak", -2)]),
}
FLASHY = {"flash_white", "flash_color", "flash_cut", "invert_flash", "negative", "flash_zoom_hook"}


# ----------------------------------------------------------------------------------------------- media io
def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
                        "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    s = j["streams"][0]
    num, den = (int(x) for x in s["r_frame_rate"].split("/"))
    return int(s["width"]), int(s["height"]), num / den, float(j["format"]["duration"])


def read_audio(path, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    return a


def lufs_of(path_or_array):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(path_or_array), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return float(m[-1]) if m else -23.0


def write_wav(path, a):
    import wave
    a = np.clip(a, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype("<i2").tobytes())


# ----------------------------------------------------------------------------------------------- apply
def window(cue):
    p = PRESETS[cue["fx"]]
    dur = cue.get("dur", p["dur"])
    t0 = cue["t"] - dur / 2 if p["centre"] == "around" else cue["t"]
    return max(0.0, t0), t0 + dur, dur


def apply(inp, cues_path, out, lufs_target=-14.0, no_sfx=False):
    W, H, fps, dur = probe(inp)
    cues = json.loads(Path(cues_path).read_text(encoding="utf-8"))["cues"]
    wins = []
    for n, c in enumerate(cues):
        t0, t1, d = window(c)
        wins.append((t0, t1, d, n, c))
    tmp_v = Path(out).with_suffix(".fxvideo.mp4")
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(inp), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", f"{fps}",
                            "-i", "-", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-pix_fmt", "yuv420p", str(tmp_v)], stdin=subprocess.PIPE)
    fsz = W * H * 3
    buf, ctxs, prev_out = [], {}, None
    k_frame = 0
    while True:
        raw = dec.stdout.read(fsz)
        if len(raw) < fsz:
            break
        img = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        t = k_frame / fps
        out_img = img
        for (t0, t1, d, n, c) in wins:
            if t0 <= t < t1:
                p = PRESETS[c["fx"]]
                u = (t - t0) / max(1e-6, d)
                k = ENV[c.get("env", p["env"])](u) * c.get("amount", 1.0)
                i = int(round((t - t0) * fps))
                ctx = ctxs.setdefault(n, dict(c.get("params", {}), amount=c.get("amount", 1.0), seed=n + 1))
                ctx["buf"], ctx["prev"], ctx["prev_out"] = buf, (buf[-2] if len(buf) > 1 else None), prev_out
                rng = np.random.default_rng(10007 * (n + 1) + k_frame)
                out_img = p["fn"](np.ascontiguousarray(out_img), float(k), float(u), i, rng, ctx)
        enc.stdin.write(np.ascontiguousarray(out_img, dtype=np.uint8).tobytes())
        buf.append(img)
        if len(buf) > 8:
            buf.pop(0)
        prev_out = out_img
        k_frame += 1
    enc.stdin.close(); enc.wait(); dec.wait()

    # ---- sound: the film's own audio + every cue's paired sounds, level-matched, then loudness-finished
    film = read_audio(inp)
    n_total = max(len(film), int(dur * SR))
    film = np.pad(film, ((0, n_total - len(film)), (0, 0)))
    film_lufs = lufs_of(inp)
    stem = np.zeros_like(film)
    man = {s["id"]: s for s in json.loads((LIB / "manifest.json").read_text(encoding="utf-8"))}
    placed = []
    if not no_sfx:
        for (t0, t1, d, n, c) in wins:
            p = PRESETS[c["fx"]]
            sfx = c.get("sfx")
            if sfx is None:
                sfx = [{"id": a, "at": b, "gain_db": g} for a, b, g in p["sfx"]]
            peak_t = t0 + (d / 2 if c.get("env", p["env"]) == "swell" else 0.0)
            for s in sfx:
                m = man.get(s["id"])
                if not m:
                    print("  no such sound:", s["id"]); continue
                anchor = {"start": t0, "peak": peak_t, "end": t1}[s.get("at", "start")]
                if p["centre"] == "around" and s.get("at", "peak") == "peak":
                    anchor = c["t"]
                start = anchor - m["sync_at"]
                a = read_audio(LIB / m["file"])
                if start < 0:
                    a = a[int(-start * SR):]; start = 0.0
                ref = m.get("lufs") or -18.0
                tier_off = {"hard": -2.0, "medium": -4.0, "soft": -7.0}.get(m.get("tier") or "medium", -4.0)
                g = 10 ** ((film_lufs + tier_off - ref + s.get("gain_db", 0)) / 20)
                i0 = int(start * SR)
                i1 = min(n_total, i0 + len(a))
                stem[i0:i1] += a[: i1 - i0] * g
                placed.append((round(anchor, 2), s["id"]))
    mix = film + stem
    peak = np.max(np.abs(mix)) + 1e-9
    if peak > 0.98:
        mix *= 0.98 / peak            # pre-limit; loudnorm brings the level back
    tmp_a = Path(out).with_suffix(".fxaudio.wav")
    write_wav(tmp_a, mix)
    # two-pass loudnorm to the delivery target
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(tmp_a), "-af", f"loudnorm=I={lufs_target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"): r.stderr.rfind("}") + 1])
    ln = (f"loudnorm=I={lufs_target}:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tmp_v), "-i", str(tmp_a), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", ln + ",aresample=48000", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    tmp_v.unlink(missing_ok=True); tmp_a.unlink(missing_ok=True)
    print(f"wrote {out}: {len(cues)} effects, {len(placed)} sounds")
    for t, sid in placed:
        print(f"   {t:7.2f}s  {sid}")


# ----------------------------------------------------------------------------------------------- plan
def load_shots(path):
    sys.path.insert(0, str(Path(__file__).parent))
    import brain
    return brain.load_shots(str(path))


def plan(project, shots_path=None, video=None, hook="warp"):
    P_ = Path(project)
    shots_path = Path(shots_path) if shots_path else P_ / "source" / "shots.js"
    S = load_shots(shots_path)
    shots = S["shots"]
    dur = S.get("duration") or shots[-1]["t1"]
    cues = []
    hook_fx = {"warp": "universe_warp", "glitch": "glitch_hook", "shock": "shockwave", "flashzoom": "flash_zoom_hook"}[hook]
    cues.append({"t": 0.0, "fx": hook_fx, "amount": 1.0, "why": "HOOK: frame 0 must break the scroll: an editor effect + an ominous hit, in the first second."})
    cut_cycle = ["glitch_cut", "zoom_cut", "whip_cut", "flash_cut", "glitch_cut", "pixel_cut"]
    punch_cycle = ["zoom_punch", "shake", "rgb_split", "chromatic", "lens_bulge"]
    ci = pi = 0
    for a, b in zip(shots, shots[1:]):
        t = b["t0"]
        out = a.get("out", "cut")
        if out in ("cut", "whip"):
            fx = cut_cycle[ci % len(cut_cycle)]; ci += 1
            cues.append({"t": t, "fx": fx, "amount": 0.9, "why": f"Chapter turn {a.get('id')}->{b.get('id')}: a pattern interrupt with its sound."})
        else:   # the kit already draws a transition: add only its sound and a light accent
            cues.append({"t": t, "fx": "rgb_split", "dur": 0.3, "amount": 0.5,
                         "sfx": [{"id": "whoosh-fast-hard" if out in ("pixelate", "dots", "mosaic") else "cinematic-drum-big", "at": "start", "gain_db": -2}],
                         "why": f"Kit transition '{out}' at {a.get('id')}->{b.get('id')}: sound it and add a light colour tear."})
    for s in shots:
        for grp in s.get("lines") or []:
            for w in grp:
                if len(w) > 2 and w[2] == "punch" and w[1] > 0.6:
                    fx = punch_cycle[pi % len(punch_cycle)]; pi += 1
                    cues.append({"t": float(w[1]), "fx": fx, "amount": 0.85, "why": f"Punch word '{w[0]}': hit it."})
        for w3 in s.get("type3d") or []:
            if w3.get("t", 0) > 0.6:
                cues.append({"t": float(w3["t"]), "fx": "shockwave", "amount": 0.8, "why": f"3D word '{w3.get('text')}' lands: a ring of force."})
    # ending accent
    cues.append({"t": max(0.0, dur - 1.1), "fx": "light_leak", "dur": 1.1, "amount": 0.8, "why": "Ending: warm light to close the loop."})
    cues = thin(sorted(cues, key=lambda c: c["t"]), dur)
    outp = P_ / "storyboard" / "fx_cues.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps({"duration": dur, "rules": "references/editor-effects-and-hook-sound.md", "cues": cues}, indent=1), encoding="utf-8")
    print(f"{len(cues)} cues -> {outp}")
    for c in cues:
        print(f"  {c['t']:6.2f}s  {c['fx']:16s} {c['why'][:80]}")
    return outp


PRIORITY = {"hook": 6, "transition": 5, "distort": 3, "camera": 3, "glitch": 3, "light": 2, "color": 2, "texture": 1, "time": 2}


def rank(c):
    why = c.get("why", "")
    if why.startswith("HOOK"):
        return 9
    if why.startswith("Chapter turn") or why.startswith("Kit transition"):
        return 7
    if why.startswith("3D word"):
        return 6
    if why.startswith("Ending"):
        return 4
    return PRIORITY.get(PRESETS[c["fx"]]["family"], 2)


def thin(cues, dur, gap=1.0):
    """editor taste: keep the most important cues first (hook > chapter turns > 3D words > endings > punch words),
    nothing within `gap` s of a kept cue, then back into time order"""
    kept = []
    for c in sorted(cues, key=lambda c: (-rank(c), c["t"])):
        if all(abs(c["t"] - k["t"]) >= gap for k in kept):
            kept.append(c)
    return sorted(kept, key=lambda c: c["t"])


# ----------------------------------------------------------------------------------------------- check
def check(cues_path):
    d = json.loads(Path(cues_path).read_text(encoding="utf-8"))
    cues = d["cues"]
    dur = d.get("duration") or (cues[-1]["t"] + 1)
    fails, warns = [], []
    first = [c for c in cues if c["t"] <= 0.3]
    if not first or PRESETS[first[0]["fx"]]["family"] not in ("hook",) and first[0]["fx"] not in ("digital_glitch", "shake", "shockwave", "zoom_punch"):
        fails.append("no hook effect in the first 0.3 s (use universe_warp / glitch_hook / shockwave / flash_zoom_hook)")
    if first and (first[0].get("sfx") == [] ):
        fails.append("the hook effect has no sound: pair it (braam, tear, a sub drop)")
    gaps = [b["t"] - a["t"] for a, b in zip(cues, cues[1:])]
    if gaps and max(gaps) > 7.0:
        warns.append(f"a {max(gaps):.1f} s stretch with no pattern interrupt (want one every 3-7 s)")
    fl = [c["t"] for c in cues if c["fx"] in FLASHY]
    for a, b in zip(fl, fl[1:]):
        if b - a < 1.0:
            fails.append(f"two flash-type effects {b - a:.2f} s apart at {a:.2f}s (photosensitivity: keep them >= 1 s apart)")
    if dur and len(cues) / dur > 0.5:
        warns.append(f"{len(cues)} effects in {dur:.0f} s: more than one per 2 s reads as noise")
    if sum(1 for c in cues if c["fx"] == "universe_warp") > 1:
        fails.append("universe_warp more than once: it is THE hook, use it once")
    for w in warns:
        print("WARN ", w)
    for f in fails:
        print("FAIL ", f)
    print("PASS" if not fails else f"{len(fails)} gate(s) failed")
    return 0 if not fails else 1


# ----------------------------------------------------------------------------------------------- gallery
def gallery(inp, at, outdir):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    W, H, fps, dur = probe(inp)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(at), "-i", str(inp), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    img = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
    tiles = []
    for name, p in PRESETS.items():
        ctx = {"buf": [img] * 4, "prev": img, "prev_out": img, "amount": 1.0, "seed": 1}
        rng = np.random.default_rng(3)
        u = 0.5 if p["env"] in ("swell",) else 0.12
        k = max(0.6, ENV[p["env"]](u))
        im = p["fn"](img.copy(), k, u, 2, rng, ctx)
        im = cv2.resize(im, (480, int(480 * H / W)))
        cv2.putText(im, name, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
        cv2.putText(im, name, (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        tiles.append(im)
    cols = 6
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[r:r + cols]) for r in range(0, len(tiles), cols)]
    sheet = np.vstack(rows)
    cv2.imwrite(str(outdir / "fx_gallery.jpg"), cv2.cvtColor(sheet, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(outdir / "fx_gallery.jpg")


def cmd_list():
    fam = {}
    for k, p in PRESETS.items():
        fam.setdefault(p["family"], []).append((k, p))
    for f, items in fam.items():
        print(f"## {f}")
        for k, p in items:
            print(f"  {k:16s} {p['dur']:.2f}s {p['centre']:6s} {p['job']}")
            print(f"  {'':16s} sound: {', '.join(s[0] for s in p['sfx']) or '-'}")


def export_catalogue(path):
    rows = [{"id": k, "family": p["family"], "dur": p["dur"], "centre": p["centre"], "envelope": p["env"], "job": p["job"],
             "avoid": p["avoid"], "sfx": [{"id": a, "at": b, "gain_db": g} for a, b, g in p["sfx"]]} for k, p in PRESETS.items()]
    Path(path).write_text(json.dumps(rows, indent=1), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list")
    e = sp.add_parser("export"); e.add_argument("-o", default=str(SKILL / "engines" / "fx_presets.json"))
    p = sp.add_parser("plan"); p.add_argument("project"); p.add_argument("--shots"); p.add_argument("--video"); p.add_argument("--hook", default="warp")
    a_ = sp.add_parser("apply"); a_.add_argument("inp"); a_.add_argument("cues"); a_.add_argument("-o", required=True); a_.add_argument("--lufs", type=float, default=-14.0); a_.add_argument("--no-sfx", action="store_true")
    g = sp.add_parser("gallery"); g.add_argument("inp"); g.add_argument("--at", type=float, default=2.0); g.add_argument("-o", required=True)
    c = sp.add_parser("check"); c.add_argument("cues")
    a = ap.parse_args()
    if a.cmd == "list":
        cmd_list()
    elif a.cmd == "export":
        export_catalogue(a.o); print(a.o)
    elif a.cmd == "plan":
        plan(a.project, a.shots, a.video, a.hook)
    elif a.cmd == "apply":
        apply(a.inp, a.cues, a.o, a.lufs, a.no_sfx)
    elif a.cmd == "gallery":
        gallery(a.inp, a.at, a.o)
    else:
        sys.exit(check(a.cues))


if __name__ == "__main__":
    main()

"""Procedural sound effects — original, synthesized, rights-clean.

Renders a timed SFX stem from a cue list. Every sound is synthesized in
this file (filtered noise sweeps, pitched sub drops, FM ticks), so there
are no third-party samples to license. Cue times come from scene events
(cuts, impacts, UI touches) in edit_decisions — never sprinkle whooshes
on a timer.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from tools.audio.procedural_score import (
    SR,
    bandpass,
    biquad_highpass,
    biquad_lowpass,
    fm_bell,
    reverb,
    write_wav,
)
from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolTier,
)


def _sweep_noise(rng, dur, f0, f1, q=1.6):
    n = int(dur * SR)
    noise = rng.uniform(-1, 1, n + 512)
    out = np.zeros(n)
    chunk = int(0.012 * SR)
    for i in range(0, n, chunk):
        frac = i / max(1, n)
        c = f0 * (f1 / f0) ** frac
        out[i:i + chunk] = bandpass(noise[i:i + chunk + 400], c, q)[: min(chunk, n - i)]
    return out


def whoosh(rng, dur=0.55, up=True):
    sig = _sweep_noise(rng, dur, 250 if up else 3500, 3500 if up else 250)
    t = np.linspace(0, 1, len(sig))
    env = np.sin(np.pi * t) ** 1.5
    return sig * env * 2.2


def impact(rng, dur=1.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(38 + 80 * np.exp(-t * 18)) / SR) * np.exp(-t * 4.0)
    crack = biquad_highpass(rng.uniform(-1, 1, n), 1800) * np.exp(-t * 60) * 0.5
    return np.tanh((sub + crack) * 1.4)


def tick(rng, freq=2200.0):
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    click = np.sin(2 * np.pi * freq * t) * np.exp(-t * 160)
    return click + 0.25 * biquad_highpass(rng.uniform(-1, 1, n), 4000) * np.exp(-t * 300)


def soft_thud(rng):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(60 + 70 * np.exp(-t * 35)) / SR) * np.exp(-t * 12)


def riser(rng, dur=1.5):
    sig = _sweep_noise(rng, dur, 300, 6000, 2.2)
    t = np.linspace(0, 1, len(sig))
    return sig * t ** 2.4 * 2.0


def shimmer(rng, freq=1318.5):
    n = int(1.6 * SR)
    return fm_bell(freq, n, ratio=2.01, index=1.2, decay=2.2) * 0.6 + fm_bell(freq * 1.5, n, ratio=3.0, index=0.8, decay=3.0) * 0.3


def glitch(rng):
    n = int(0.18 * SR)
    sig = np.zeros(n)
    for k in range(6):
        a = int(rng.integers(0, n - 800))
        sig[a:a + 600] += rng.uniform(-1, 1, 600) * rng.uniform(0.3, 1.0)
    return biquad_lowpass(sig, 6000)


SOUNDS = {
    "whoosh": lambda r, c: whoosh(r, c.get("duration", 0.55), c.get("direction", "up") == "up"),
    "impact": lambda r, c: impact(r),
    "tick": lambda r, c: tick(r, c.get("freq", 2200.0)),
    "thud": lambda r, c: soft_thud(r),
    "riser": lambda r, c: riser(r, c.get("duration", 1.5)),
    "shimmer": lambda r, c: shimmer(r, c.get("freq", 1318.5)),
    "glitch": lambda r, c: glitch(r),
}
# Sounds whose musical "hit" is at the END (cue time = arrival moment).
ARRIVE_AT_END = {"riser"}
# Whooshes peak in the middle: centre them on the cue time.
CENTERED = {"whoosh"}


class ProceduralSFX(BaseTool):
    name = "procedural_sfx"
    version = "0.1.0"
    tier = ToolTier.CORE
    capability = "audio_processing"
    provider = "local_procedural"
    stability = ToolStability.EXPERIMENTAL
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.DETERMINISTIC
    runtime = ToolRuntime.LOCAL

    dependencies = ["python:numpy", "python:scipy"]
    install_instructions = "pip install numpy scipy (no API key)."
    agent_skills = ["sound-effects"]
    capabilities = ["sfx_synthesis", "sfx_stem"]
    best_for = ["Rights-clean UI ticks, whooshes, impacts, risers placed on scene events"]
    not_good_for = ["Foley that must sound like a specific real-world recording"]

    input_schema = {
        "type": "object",
        "required": ["output_path", "duration_seconds", "cues"],
        "properties": {
            "output_path": {"type": "string"},
            "duration_seconds": {"type": "number"},
            "cues": {
                "type": "array",
                "description": "{time, type (" + "|".join(SOUNDS) + "), gain_db, pan (-1..1), reason}",
                "items": {"type": "object"},
            },
            "seed": {"type": "integer", "default": 3},
        },
    }
    resource_profile = ResourceProfile(cpu_cores=1, ram_mb=300, vram_mb=0, disk_mb=20)
    idempotency_key_fields = ["duration_seconds", "cues", "seed"]
    side_effects = ["writes stereo SFX stem WAV + .json cue sidecar"]

    def estimate_cost(self, inputs: dict[str, Any]) -> float:
        return 0.0

    def execute(self, inputs: dict[str, Any]) -> ToolResult:
        t0 = time.time()
        rng = np.random.default_rng(int(inputs.get("seed", 3)))
        dur = float(inputs["duration_seconds"])
        n = int(dur * SR) + SR
        L = np.zeros(n)
        R = np.zeros(n)
        placed = []
        for cue in inputs["cues"]:
            kind = cue.get("type")
            if kind not in SOUNDS:
                return ToolResult(success=False, error=f"Unknown SFX type {kind!r}; options: {sorted(SOUNDS)}")
            sig = SOUNDS[kind](rng, cue)
            if kind in ("impact", "shimmer", "whoosh"):
                sig = reverb(sig, room=0.7, wet=0.25)
            g = 10 ** (float(cue.get("gain_db", -6)) / 20)
            t = float(cue["time"])
            if kind in ARRIVE_AT_END:
                t -= len(sig) / SR
            elif kind in CENTERED:
                t -= len(sig) / SR / 2
            s = int(max(0.0, t) * SR)
            e = min(n, s + len(sig))
            pan = float(cue.get("pan", 0.0))
            lg, rg = np.sqrt((1 - pan) / 2) * np.sqrt(2), np.sqrt((1 + pan) / 2) * np.sqrt(2)
            L[s:e] += sig[: e - s] * g * lg
            R[s:e] += sig[: e - s] * g * rg
            placed.append({**cue, "start_sample_s": round(s / SR, 4)})
        mix = np.stack([L, R], axis=1)[: int(dur * SR)]
        peak = np.max(np.abs(mix)) + 1e-9
        if peak > 0.89:
            mix *= 0.89 / peak
        out = Path(inputs["output_path"])
        write_wav(out, mix)
        meta = {
            "output": str(out),
            "cues": placed,
            "provenance": {
                "source": "original synthesized SFX",
                "generator": f"OpenMontage tools/audio/procedural_sfx.py v{self.version}",
                "samples_used": "none",
                "third_party_audio": False,
            },
        }
        out.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return ToolResult(success=True, data=meta, artifacts=[str(out)], duration_seconds=round(time.time() - t0, 2), cost_usd=0.0)

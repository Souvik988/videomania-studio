"""Audio stage: VO cleanup, music (supplied or original), SFX, ducked master.

Usage:
  make_audio.py --project ID [--plan storyboard/audio_plan.json]
  make_audio.py --analyze-track PATH          # beat/tempo analysis only

audio_plan.json:
{
  "music": {"source": "procedural" | "user", "user_track": "path", "license": "...",
            "mood": "tension_to_release", "sections": [...], "anchors": [15.6], "seed": 11,
            "volume": 0.35},
  "sfx": [{"time": 1.2, "type": "whoosh", "gain_db": -12, "reason": "S01->S02 push"}],
  "mix": {"loudness_target": -14, "music_volume_during_speech": 0.14,
          "attack_ms": 120, "release_ms": 450}
}

Writes audio/vo_clean.wav, audio/stems/{music,sfx,voice}.wav, audio/mix.wav,
qa/audio_report.json. Narration stays the timing master: nothing here moves
or time-stretches the voice.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402

# Speech chain: rumble cut, mud dip, presence lift, gentle de-ess, light
# compression. No loudnorm here — the master stage sets final loudness once.
VO_CHAIN = (
    "highpass=f=75,"
    "equalizer=f=250:t=q:w=1.2:g=-2,"
    "equalizer=f=3200:t=q:w=1.0:g=2,"
    "deesser=i=0.35:m=0.5:f=0.5:s=o,"
    "acompressor=threshold=-21dB:ratio=2.5:attack=8:release=120:makeup=2"
)


def analyze_track(path: Path) -> dict:
    """Estimate tempo, beat grid and (approximate) downbeats of a music file.

    Spectral-flux onset envelope -> autocorrelation tempo (60-180 BPM) ->
    beat phase maximising onset energy -> downbeat phase chosen by low-band
    onset energy on candidate bar positions. Downbeats are an ESTIMATE;
    callers must not treat every 4th beat as a verified downbeat.
    """
    import numpy as np
    import soundfile as sf
    from scipy.signal import stft

    tmp = path.with_name(path.stem + ".analysis.wav")
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-ac", "1", "-ar", "22050", str(tmp)])
    x, sr = sf.read(str(tmp))
    tmp.unlink(missing_ok=True)
    hop = 256
    f, t, Z = stft(x, sr, nperseg=1024, noverlap=1024 - hop)
    mag = np.log1p(np.abs(Z) * 100)
    flux = np.maximum(0, np.diff(mag, axis=1))
    onset = flux.sum(0)
    low = flux[f[:-0 or None][: flux.shape[0]] < 200].sum(0) if True else onset
    onset = (onset - onset.mean()) / (onset.std() + 1e-9)
    fps = sr / hop
    ac = np.correlate(onset, onset, mode="full")[len(onset) - 1:]
    lags = np.arange(len(ac))
    bpms = 60 * fps / np.maximum(lags, 1)
    mask = (bpms >= 60) & (bpms <= 180)
    # prefer the 80-140 region (perceptual weighting)
    weight = np.exp(-0.5 * ((bpms - 110) / 40) ** 2)
    cand = np.where(mask, ac * weight, -np.inf)
    lag = int(np.argmax(cand))
    # parabolic refinement
    if 1 <= lag < len(ac) - 1:
        a, b, c = ac[lag - 1], ac[lag], ac[lag + 1]
        lag = lag + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    bpm = 60 * fps / lag
    period = fps * 60 / bpm
    best_phase, best_score = 0.0, -1e9
    for ph in np.linspace(0, period, 64, endpoint=False):
        idx = (np.arange(ph, len(onset), period)).astype(int)
        s = onset[idx].sum()
        if s > best_score:
            best_phase, best_score = ph, s
    beat_frames = np.arange(best_phase, len(onset), period)
    beats = [round(float(b / fps), 4) for b in beat_frames]
    low_n = (low - low.mean()) / (low.std() + 1e-9)
    bar_scores = []
    for k in range(4):
        idx = beat_frames[k::4].astype(int)
        idx = idx[idx < len(low_n)]
        bar_scores.append(float(low_n[idx].mean()) if len(idx) else -9)
    k = int(np.argmax(bar_scores))
    confidence = float((sorted(bar_scores)[-1] - sorted(bar_scores)[-2]) / (np.std(bar_scores) + 1e-9))
    return {
        "path": str(path),
        "bpm": round(float(bpm), 2),
        "beats": beats,
        "downbeats_estimated": beats[k::4],
        "downbeat_phase_confidence": round(confidence, 2),
        "method": "spectral-flux autocorrelation; downbeats estimated from low-band onset energy (not verified)",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--plan", default="storyboard/audio_plan.json")
    ap.add_argument("--analyze-track")
    args = ap.parse_args()
    vm_env.ensure_openmontage_on_path()

    if args.analyze_track:
        print(vm_env.json.dumps(analyze_track(Path(args.analyze_track)), indent=2)[:4000])
        return 0

    proj = vm_env.project_dir(args.project)
    plan = vm_env.read_json(proj / args.plan)
    src = vm_env.read_json(proj / "input" / "SOURCE.json")
    vo_src = Path(src["copy"])
    if any(st["codec_type"] == "video" for st in vm_env.ffprobe(vo_src)["streams"]):
        # EDIT mode: the clip's own dialogue is the speech track
        extracted = proj / "audio" / "source_dialogue.wav"
        extracted.parent.mkdir(parents=True, exist_ok=True)
        vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(vo_src), "-vn", "-ac", "1", "-ar", "48000", "-c:a", "pcm_s24le", str(extracted)])
        vo_src = extracted
    duration = float(vm_env.ffprobe(vo_src)["format"]["duration"])
    tail = float(plan.get("tail_seconds", 1.5))
    total = duration + tail
    stems = proj / "audio" / "stems"
    stems.mkdir(parents=True, exist_ok=True)
    report: dict = {"vo_source": str(vo_src), "vo_duration_s": duration, "total_duration_s": total}

    # 1. VO cleanup on a copy (OpenMontage audio_enhance, custom chain)
    from tools.audio.audio_enhance import AudioEnhance
    vo_clean = proj / "audio" / "vo_clean.wav"
    # apad: full_mix ends with the speech input, so the voice stem must already
    # span the tail or the music ring-out under the end card is cut off.
    r = AudioEnhance().execute({"input_path": str(vo_src), "output_path": str(vo_clean),
                                "custom_af": VO_CHAIN + f",aresample=48000,pan=stereo|c0=c0|c1=c0,apad=whole_dur={total:.3f}",
                                "audio_codec": "pcm_s24le",
                                "audio_bitrate": "1536k"})
    if not r.success:
        print(f"FAILED: audio_enhance: {r.error}")
        return 1
    shutil.copy2(vo_clean, stems / "voice.wav")
    report["vo_chain"] = VO_CHAIN

    # 2. music
    music_cfg = plan.get("music") or {}
    music_path = stems / "music.wav"
    if music_cfg.get("source") == "none":
        report["music"] = {"source": "none", "reason": music_cfg.get("reason", "user requested no music")}
        music_path = None
    elif music_cfg.get("source") == "user":
        track = Path(music_cfg["user_track"])
        fade_out = max(0.0, total - 2.0)
        vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(track), "-t", f"{total:.3f}", "-af",
                    f"afade=t=in:d=0.8,afade=t=out:st={fade_out:.3f}:d=2,aresample=48000", "-ac", "2",
                    "-c:a", "pcm_s24le", str(music_path)])
        report["music"] = {"source": "user", "track": str(track), "license": music_cfg.get("license", "UNSPECIFIED — confirm rights"),
                           "analysis": analyze_track(track)}
    else:
        from tools.audio.procedural_score import ProceduralScore
        r = ProceduralScore().execute({
            "output_path": str(music_path), "duration_seconds": total,
            "mood": music_cfg.get("mood", "tension_to_release"), "sections": music_cfg.get("sections", []),
            "anchors": music_cfg.get("anchors", []), "seed": int(music_cfg.get("seed", 11)),
            "stems_dir": str(stems / "music_parts"), **({"bpm": music_cfg["bpm"]} if music_cfg.get("bpm") else {}),
            **({"key": music_cfg["key"]} if music_cfg.get("key") else {}),
            **({"scale": music_cfg["scale"]} if music_cfg.get("scale") else {}),
        })
        if not r.success:
            print(f"FAILED: procedural_score: {r.error}")
            return 1
        report["music"] = {"source": "procedural_score", **{k: r.data[k] for k in ("bpm", "key", "scale", "mood", "beat_grid_offset", "anchor_mean_error_s", "provenance")},
                           "downbeats": r.data["downbeats"]}

    # 3. SFX
    sfx_path = None
    if plan.get("sfx"):
        from tools.audio.procedural_sfx import ProceduralSFX
        sfx_path = stems / "sfx.wav"
        r = ProceduralSFX().execute({"output_path": str(sfx_path), "duration_seconds": total, "cues": plan["sfx"]})
        if not r.success:
            print(f"FAILED: procedural_sfx: {r.error}")
            return 1
        report["sfx"] = {"cues": len(plan["sfx"]), "provenance": r.data["provenance"]}

    # 4. master via OpenMontage audio_mixer full_mix (sidechain ducking + loudnorm)
    mix_cfg = plan.get("mix", {})
    target = float(mix_cfg.get("loudness_target", -14))
    tracks = [{"path": str(vo_clean), "role": "speech", "start_seconds": float(plan.get("vo_offset_seconds", 0))}]
    if music_path:
        tracks.append({"path": str(music_path), "role": "music", "volume": float(music_cfg.get("volume", 0.35))})
    if sfx_path:
        tracks.append({"path": str(sfx_path), "role": "sfx", "volume": float(mix_cfg.get("sfx_volume", 0.8))})
    from tools.audio.audio_mixer import AudioMixer
    mix_path = proj / "audio" / "mix.wav"
    r = AudioMixer().execute({
        "operation": "full_mix", "tracks": tracks, "output_path": str(mix_path), "normalize": True,
        "loudnorm_target": target, "target_duration": total,
        "ducking": {"enabled": True, "music_volume_during_speech": float(mix_cfg.get("music_volume_during_speech", 0.14)),
                    "attack_ms": int(mix_cfg.get("attack_ms", 120)), "release_ms": int(mix_cfg.get("release_ms", 450))},
    })
    if not r.success:
        print(f"FAILED: audio_mixer full_mix: {r.error}")
        return 1

    # 5. measured trim: single-pass loudnorm on short programmes lands ~1 LU off.
    #    Apply the exact static gain to the target, then a true-peak-safe limiter.
    pre = vm_env.loudness(mix_path)
    report["mix_loudness_pre_trim"] = pre
    #    Always limited: AAC encoding adds inter-sample peaks, and the delivered file must
    #    measure <= -1.5 dBTP (herk-edit-kit house rule), so the WAV limits at -2.6 dBFS.
    gain = target - pre.get("integrated_lufs", target)
    trimmed = mix_path.with_name("mix.trim.wav")
    vm_env.run(["ffmpeg", "-y", "-v", "error", "-i", str(mix_path), "-af",
                f"volume={gain:.2f}dB,alimiter=limit=0.74:attack=2:release=60:level=disabled,aresample=48000",
                "-c:a", "pcm_s24le", str(trimmed)])
    trimmed.replace(mix_path)
    report["trim_db"] = round(gain, 2)

    # 6. measure — never trust the plan
    chans = [st.get("channels") for st in vm_env.ffprobe(mix_path)["streams"] if st["codec_type"] == "audio"]
    report["mix_channels"] = chans[0] if chans else None
    if music_path and report["mix_channels"] != 2:
        print(f"FAILED: master mix has {report['mix_channels']} channel(s); expected stereo (music stem is stereo)")
        return 1
    report["mix_loudness"] = vm_env.loudness(mix_path)
    report["voice_loudness"] = vm_env.loudness(vo_clean)
    if music_path:
        report["music_stem_loudness"] = vm_env.loudness(music_path)
    report["loudness_target"] = target
    lm = report["mix_loudness"]
    report["checks"] = {
        "integrated_within_1lu": abs(lm.get("integrated_lufs", -99) - target) <= 1.0,
        "true_peak_le_minus1p5": lm.get("true_peak_dbtp", 9) <= -1.5,
    }
    vm_env.write_json(proj / "qa" / "audio_report.json", report)
    print(vm_env.json.dumps({"mix": str(mix_path), "loudness": lm, "checks": report["checks"],
                             "music": {k: v for k, v in report.get("music", {}).items() if k in ("source", "bpm", "anchor_mean_error_s")}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

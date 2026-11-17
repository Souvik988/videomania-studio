"""vm media: the edits an NLE does to footage, for an agent. Every command writes a new file (sources are never
changed) and, where it belongs on the timeline, places it with `opsgen edit` (OpsGen, the film's openfilm/ folder).

    vm media reverse   <in> -o <out>                         play backwards (picture + sound); clips up to ~60 s
    vm media stabilize <in> -o <out> [--smooth 15]           two-pass vid.stab, slight zoom to hide the edges, sharpened
    vm media denoise   <in> -o <out> [--strength 25]         voice clean-up: rumble cut, FFT noise reduction, de-hiss
    vm media key       <in> -o <out.webm> [--color 00ff00] [--similarity 0.12] [--blend 0.06]
                                                             chroma key -> VP9 with alpha (hard cases: greenscreen_key.py)
    vm media reframe   <in> -o <out> [--aspect 9:16] [--follow auto|motion|saliency|depth|center] [--deadzone 0.08]
                                                             auto-reframe: a virtual camera follows the subject, eased
    vm media track     <in> --at <s> --box x,y,w,h [--until <s>] [--film F --attach <clip id>]
                                                             motion tracking (CSRT): keyframes that pin an overlay to it
    vm media beats     <music> [--film F]                    tempo, beats, downbeats, section entries (cut points)
    vm media broll     <film> --src <file> --word <w> [--nth 1] [--dur 2] [--mode full|pip|split] [--offset 0]
                                                             put a picture or clip on a spoken word, faded in and out

Why: the user asked that no edit be impossible in Claude Editor (OpsGen). Speed ramps, freezes, splits, keyframes,
fades and ripples are timeline operations (`opsgen edit`); these are the ones that need new pixels or sound.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

S = Path(__file__).resolve().parent
sys.path.insert(0, str(S))
import vm_env  # noqa: E402


# ---------------------------------------------------------------------------------------------------- helpers
def ff(args, cwd=None):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], capture_output=True, text=True, cwd=cwd)
    if r.returncode:
        raise SystemExit(f"ffmpeg failed: {r.stderr[-1500:]}")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate",
                        "-show_entries", "format=duration", "-of", "json", str(path)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), None)
    a = any(s.get("codec_type") == "audio" for s in j["streams"])
    fps = 30.0
    if v and v.get("r_frame_rate"):
        n, d = (int(x) for x in v["r_frame_rate"].split("/"))
        fps = n / d if d else 30.0
    return {"w": v and int(v["width"]), "h": v and int(v["height"]), "fps": fps, "dur": float(j["format"]["duration"]), "audio": a}


def frames(path, w, h, fps=None, size=None):
    """decode frames as RGB arrays; size=(sw, sh) scales, fps resamples"""
    vf = []
    if fps:
        vf.append(f"fps={fps}")
    if size:
        vf.append(f"scale={size[0]}:{size[1]}")
        w, h = size
    cmd = ["ffmpeg", "-v", "error", "-i", str(path)] + (["-vf", ",".join(vf)] if vf else []) + ["-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = w * h * 3
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    p.wait()


def project_film(film):
    p = Path(film)
    if not p.is_dir():
        p = vm_env.workbench() / "OpenMontage" / "projects" / film
    if not p.is_dir():
        raise SystemExit(f"no film {film}")
    return p


def opsgen_edit(p: Path, ops):
    import vm_openfilm as of
    r = of._run([*of.OF, "edit", json.dumps(ops), "--film", p / "openfilm"], check=False, timeout=300)
    if r.returncode:
        raise SystemExit((r.stdout + r.stderr)[-1500:])
    return r.stdout.strip()


# ---------------------------------------------------------------------------------------------------- pixel and sound ops
def reverse(a):
    info = probe(a.inp)
    if info["dur"] > 75:
        raise SystemExit(f"{a.inp} is {info['dur']:.0f} s: reverse a trimmed part (<= 60 s; it is held in memory)")
    args = ["-i", a.inp, "-vf", "reverse"] + (["-af", "areverse"] if info["audio"] else []) + ["-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", a.o]
    ff(args)
    return {"made": a.o, "seconds": round(info["dur"], 2)}


def stabilize(a):
    with tempfile.TemporaryDirectory() as td:
        src = Path(a.inp).resolve()
        ff(["-i", src, "-vf", "vidstabdetect=shakiness=6:accuracy=15:result=motion.trf", "-f", "null", "-"], cwd=td)
        ff(["-i", src, "-vf", f"vidstabtransform=input=motion.trf:smoothing={a.smooth}:zoom=3:optzoom=0,unsharp=5:5:0.7:3:3:0.3",
            "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", Path(a.o).resolve()], cwd=td)
    return {"made": a.o, "smoothing": a.smooth}


def denoise(a):
    af = f"highpass=f=75,afftdn=nf=-{a.strength}:tn=1,deesser=i=0.3,lowpass=f=14000"
    info = probe(a.inp)
    if info["w"]:
        ff(["-i", a.inp, "-c:v", "copy", "-af", af, "-c:a", "aac", "-b:a", "256k", a.o])
    else:
        ff(["-i", a.inp, "-af", af, a.o])
    return {"made": a.o, "chain": af}


def key(a):
    c = a.color.lstrip("#")
    spill = "green" if c.lower().startswith("00") and c[2:4].lower() in ("ff", "fe", "e0", "c0") else "blue"
    ff(["-i", a.inp, "-vf", f"chromakey=0x{c}:{a.similarity}:{a.blend},despill={spill}", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0", "-b:v", "0", "-crf", "24", "-an", a.o])
    return {"made": a.o, "alpha": True, "note": "for hair, motion blur or uneven light use greenscreen_key.py (clean plate, relight)"}


# ---------------------------------------------------------------------------------------------------- reframe
def spectral_saliency(g):
    """spectral residual saliency (Hou & Zhang 2007) on a small grey frame"""
    f = np.fft.fft2(g)
    la = np.log(np.abs(f) + 1e-6)
    ph = np.angle(f)
    k = np.ones((3, 3)) / 9
    from numpy.lib.stride_tricks import sliding_window_view
    pad = np.pad(la, 1, mode="edge")
    avg = (sliding_window_view(pad, (3, 3)) * k).sum(axis=(-1, -2))
    sal = np.abs(np.fft.ifft2(np.exp((la - avg) + 1j * ph))) ** 2
    return sal / (sal.max() + 1e-9)


def depth_session():
    import onnxruntime as ort
    import vm_depth
    so = ort.SessionOptions()
    so.intra_op_num_threads = 4
    return ort.InferenceSession(vm_depth.model_path(), sess_options=so, providers=["CPUExecutionProvider"])


def depth_map(sess, rgb):
    import cv2
    h, w = rgb.shape[:2]
    s = 252 / max(w, h)
    tw, th = max(14, round(w * s / 14) * 14), max(14, round(h * s / 14) * 14)
    x = cv2.resize(rgb, (tw, th)).astype(np.float32) / 255.0
    x = ((x - (0.485, 0.456, 0.406)) / (0.229, 0.224, 0.225)).astype(np.float32).transpose(2, 0, 1)[None]
    d = np.squeeze(sess.run(None, {sess.get_inputs()[0].name: x})[0]).astype(np.float32)
    lo, hi = np.percentile(d, 2), np.percentile(d, 98)
    return cv2.resize(np.clip((d - lo) / max(hi - lo, 1e-6), 0, 1), (w, h))


def reframe(a):
    import cv2
    info = probe(a.inp)
    W, H, fps = info["w"], info["h"], info["fps"]
    num, den = (int(x) for x in a.aspect.split(":"))
    target = num / den
    if W / H > target:            # crop the width (16:9 -> 9:16, 4:5, 1:1)
        cw, ch = int(round(H * target / 2) * 2), H
    else:                         # crop the height
        cw, ch = W, int(round(W / target / 2) * 2)
    out_w, out_h = (1080, int(round(1080 / target / 2) * 2)) if target < 1 else (int(round(1080 * target / 2) * 2), 1080)

    # 1. where the subject is, 6 times a second, on small frames; where the cuts are
    sw = 320
    sh = int(round(H * sw / W / 2) * 2)
    rate = 6
    use_depth = a.follow == "depth" or (a.follow == "auto" and not a.no_depth)
    sess = depth_session() if use_depth else None
    step = 1 if info["dur"] < 90 else 3                       # depth every sample on short clips
    xs, ys, diffs, prev, dmap = [], [], [], None, None
    gx, gy = np.meshgrid(np.linspace(-1, 1, sw), np.linspace(-1, 1, sh))
    bias = np.exp(-(gx ** 2 * 0.8 + gy ** 2 * 1.2))           # a little centre bias, as camera operators frame
    for i, fr in enumerate(frames(a.inp, W, H, fps=rate, size=(sw, sh))):
        g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        diffs.append(float(np.abs(g - prev).mean()) if prev is not None else 0.0)
        score = np.zeros_like(g)
        if a.follow in ("saliency", "auto"):
            small = cv2.resize(g, (128, max(8, int(128 * sh / sw))))
            score += 0.6 * cv2.resize(cv2.GaussianBlur(spectral_saliency(small), (0, 0), 2), (sw, sh))
        if a.follow in ("motion", "auto") and prev is not None and diffs[-1] < 0.12:   # no motion across a cut
            m = cv2.GaussianBlur(np.abs(g - prev), (0, 0), 4)
            score += 0.8 * m / (m.max() + 1e-6)
        if sess is not None:
            if i % step == 0 or dmap is None or diffs[-1] >= 0.12:
                dmap = depth_map(sess, fr)
            score += 2.0 * dmap ** 3                           # the nearest thing is usually the subject
        prev = g
        if a.follow == "center" or score.max() <= 0:
            xs.append(0.5); ys.append(0.5); continue
        score = score * bias
        thr = np.quantile(score, 0.97)
        w8 = np.where(score >= thr, score, 0)
        tot = w8.sum() + 1e-9
        xs.append(float((w8 * (gx + 1) / 2).sum() / tot))
        ys.append(float((w8 * (gy + 1) / 2).sum() / tot))
    if not xs:
        raise SystemExit("no frames read")
    cut_samples = [0] + [i for i, d in enumerate(diffs) if i > 0 and d >= 0.12]

    # 2. a camera operator, not a jitter: a new framing on every cut (opened on the subject), inside a shot a dead
    #    zone and an eased move (forward-backward smoothing)
    n_out = int(round(info["dur"] * fps))
    t_s = np.arange(len(xs)) / rate
    t_f = np.arange(n_out) / fps
    bounds = sorted(set([min(n_out, int(round(c / rate * fps))) for c in cut_samples] + [n_out]))

    def camera(vals, span):
        v = np.interp(t_f, t_s, np.array(vals))
        cam = np.empty_like(v)
        dz = a.deadzone * span
        alpha = 1 - math.exp(-1 / (fps * 0.45))              # ~0.45 s time constant
        for s0, s1 in zip(bounds, bounds[1:]):
            if s1 <= s0:
                continue
            seg = v[s0:s1]
            c = float(np.median(seg[: max(1, int(0.5 * fps))]))
            out = np.empty_like(seg)
            for k, x in enumerate(seg):
                if abs(x - c) > dz:
                    c = x - math.copysign(dz, x - c)
                out[k] = c
            for rng in (range(len(out)), range(len(out) - 1, -1, -1)):
                acc = None
                for k in rng:
                    acc = out[k] if acc is None else acc + alpha * (out[k] - acc)
                    out[k] = acc
            cam[s0:s1] = out
        return cam
    camx = camera(xs, cw / W)
    camy = camera(ys, ch / H)

    # 3. crop every frame at full resolution and encode
    tmp = Path(a.o).with_suffix(".video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cw}x{ch}", "-r", f"{fps}", "-i", "-",
                            "-vf", f"scale={out_w}:{out_h}:flags=lanczos", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", str(tmp)],
                           stdin=subprocess.PIPE)
    for k, fr in enumerate(frames(a.inp, W, H)):
        j = min(k, n_out - 1)
        x0 = int(np.clip(camx[j] * W - cw / 2, 0, W - cw))
        y0 = int(np.clip(camy[j] * H - ch / 2, 0, H - ch))
        enc.stdin.write(np.ascontiguousarray(fr[y0:y0 + ch, x0:x0 + cw]).tobytes())
    enc.stdin.close(); enc.wait()
    if info["audio"]:
        ff(["-i", tmp, "-i", a.inp, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", a.o])
        tmp.unlink(missing_ok=True)
    else:
        shutil.move(tmp, a.o)
    moves = float(np.abs(np.diff(camx)).sum() * W)
    return {"made": a.o, "size": f"{out_w}x{out_h}", "follow": a.follow, "depth": use_depth, "cuts": [round(c / rate, 2) for c in cut_samples[1:]], "camera_travel_px": round(moves), "samples": len(xs)}


# ---------------------------------------------------------------------------------------------------- tracking
def track(a):
    import cv2
    info = probe(a.inp)
    W, H, fps = info["w"], info["h"], info["fps"]
    x, y, w, h = (int(float(v)) for v in a.box.split(","))
    t0, t1 = a.at, a.until if a.until is not None else info["dur"]
    scale = min(1.0, 960 / W)                      # track on a smaller copy: much faster, same path
    sw, sh = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", str(a.inp), "-vf", f"scale={sw}:{sh}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    n = sw * sh * 3
    tr = cv2.TrackerCSRT_create()
    path, k, lost = [], 0, 0
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        fr = np.frombuffer(b, np.uint8).reshape(sh, sw, 3)
        if k == 0:
            tr.init(fr, (int(x * scale), int(y * scale), max(4, int(w * scale)), max(4, int(h * scale))))
            ok, bb = True, (x * scale, y * scale, w * scale, h * scale)
        else:
            ok, bb = tr.update(fr)
        if not ok:
            lost += 1
            bb = path[-1][1] if path else (x * scale, y * scale, w * scale, h * scale)
        cx, cy = (bb[0] + bb[2] / 2) / scale, (bb[1] + bb[3] / 2) / scale
        path.append((round(t0 + k / fps, 3), bb, round(cx, 1), round(cy, 1)))
        k += 1
    p.wait()
    if not path:
        raise SystemExit("no frames tracked")
    # keyframes: ~16 evenly spaced points, as translate offsets from the first position (source pixels; times stage
    # pixels when the clip fills the stage: --stage-scale)
    idx = np.linspace(0, len(path) - 1, min(16, len(path))).round().astype(int)
    c0x, c0y = path[0][2], path[0][3]
    frames_kf = {}
    for i in idx:
        pct = 0 if len(path) == 1 else round(100 * i / (len(path) - 1), 2)
        frames_kf[f"{pct}%"] = f"translate: {round((path[i][2] - c0x) * a.stage_scale, 1)}px {round((path[i][3] - c0y) * a.stage_scale, 1)}px"
    op = {"op": "kf", "id": a.attach or "<overlay clip id>", "name": f"track-{a.attach or 'overlay'}", "frames": frames_kf,
          "dur": round(path[-1][0] - path[0][0], 3), "ease": "linear"}
    res = {"frames": len(path), "lost": lost, "from": path[0][0], "to": path[-1][0],
           "samples": [[q[0], q[2], q[3]] for q in path[:: max(1, len(path) // 8)]],
           "start_center": [c0x, c0y], "end_center": [path[-1][2], path[-1][3]], "kf_op": op}
    if a.film and a.attach:
        res["applied"] = opsgen_edit(project_film(a.film), [op])
    return res


# ---------------------------------------------------------------------------------------------------- beats / broll
def beats(a):
    out = Path(tempfile.gettempdir()) / "vm_beats.json"
    r = subprocess.run([str(vm_env.venv_python()), str(S / "music_map.py"), str(a.music), "-o", str(out)], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])
    m = json.loads(out.read_text(encoding="utf-8"))
    m = m.get("tracks", m) if isinstance(m, dict) else m
    t = next(iter(m.values())) if isinstance(m, dict) else m[0]
    return {"music": str(a.music), "bpm": round(t.get("bpm", 0)), "key": t.get("key"),
            "downbeats": [round(x, 3) for x in t.get("downbeats", [])][:64],
            "entries": [round(x, 3) for x in t.get("entries", [])], "character": t.get("character"),
            "use": "cut on downbeats; enter songs on entries (sound_mix.py --cue file@<entry>:t0-t1)"}


def broll(a):
    p = project_film(a.film)
    words = json.loads((p / "transcript" / "words.json").read_text(encoding="utf-8"))
    words = words.get("words", words) if isinstance(words, dict) else words
    want = a.word.lower().strip(".,!?")
    hits = [w for w in words if w.get("word", w.get("text", "")).lower().strip(" .,!?") == want]
    if len(hits) < a.nth:
        raise SystemExit(f"'{a.word}' is said {len(hits)} time(s); --nth {a.nth} is too many")
    t = round(hits[a.nth - 1]["start"] + a.offset, 3)
    src = Path(a.src)
    dst_dir = p / "openfilm" / "assets" / "broll"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    if not dst.exists():
        shutil.copy2(src, dst)
    rel = f"assets/broll/{src.name}"
    still = src.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif")
    st = json.loads((p / "vm.json").read_text(encoding="utf-8")) if (p / "vm.json").exists() else {}
    import brain
    S_ = brain.load_shots(str(p / "source" / "shots.js")) if (p / "source" / "shots.js").exists() else {"size": [1920, 1080]}
    SW, SH = S_.get("size", [1920, 1080])
    box = {"full": {"x": 0, "y": 0, "w": SW, "h": SH},
           "pip": {"x": round(SW * 0.62), "y": round(SH * 0.08), "w": round(SW * 0.33), "h": round(SH * 0.33)},
           "split": {"x": round(SW / 2), "y": 0, "w": round(SW / 2), "h": SH}}[a.mode]
    style = "object-fit: cover" + ("; border-radius: 24px; box-shadow: 0 20px 60px rgba(0,0,0,.45)" if a.mode == "pip" else "")
    add = {"op": "add", "src": rel, "at": t, "track": "new-top", "id": f"broll-{src.stem}", "box": box, "style": style,
           **({"in": 0, "out": a.dur} if still else {"in": a.src_in, "len": a.dur, "volume": 0})}
    said = opsgen_edit(p, [add])
    clip_id = next((l.split()[1] for l in said.splitlines() if l.startswith("added ")), f"broll-{src.stem}")
    opsgen_edit(p, [{"op": "fade", "id": clip_id, "in": 0.15, "out": 0.2}])
    return {"word": a.word, "at": t, "clip": clip_id, "mode": a.mode, "timeline": said.splitlines()[-12:]}


# ---------------------------------------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(prog="vm media", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="op", required=True)
    x = sp.add_parser("reverse"); x.add_argument("inp"); x.add_argument("-o", required=True); x.set_defaults(fn=reverse)
    x = sp.add_parser("stabilize"); x.add_argument("inp"); x.add_argument("-o", required=True); x.add_argument("--smooth", type=int, default=15); x.set_defaults(fn=stabilize)
    x = sp.add_parser("denoise"); x.add_argument("inp"); x.add_argument("-o", required=True); x.add_argument("--strength", type=int, default=25); x.set_defaults(fn=denoise)
    x = sp.add_parser("key"); x.add_argument("inp"); x.add_argument("-o", required=True); x.add_argument("--color", default="00ff00"); x.add_argument("--similarity", type=float, default=0.12); x.add_argument("--blend", type=float, default=0.06); x.set_defaults(fn=key)
    x = sp.add_parser("reframe"); x.add_argument("inp"); x.add_argument("-o", required=True); x.add_argument("--aspect", default="9:16"); x.add_argument("--follow", default="auto", choices=["auto", "motion", "saliency", "depth", "center"]); x.add_argument("--deadzone", type=float, default=0.08); x.add_argument("--no-depth", action="store_true", help="auto without the depth model (faster)"); x.set_defaults(fn=reframe)
    x = sp.add_parser("track"); x.add_argument("inp"); x.add_argument("--at", type=float, required=True); x.add_argument("--box", required=True); x.add_argument("--until", type=float); x.add_argument("--film"); x.add_argument("--attach"); x.add_argument("--stage-scale", type=float, default=1.0); x.set_defaults(fn=track)
    x = sp.add_parser("beats"); x.add_argument("music"); x.add_argument("--film"); x.set_defaults(fn=beats)
    x = sp.add_parser("broll"); x.add_argument("film"); x.add_argument("--src", required=True); x.add_argument("--word", required=True); x.add_argument("--nth", type=int, default=1); x.add_argument("--dur", type=float, default=2.0); x.add_argument("--mode", default="pip", choices=["full", "pip", "split"]); x.add_argument("--offset", type=float, default=0.0); x.add_argument("--src-in", type=float, default=0.0); x.set_defaults(fn=broll)
    a = ap.parse_args(argv)
    res = a.fn(a)
    print(json.dumps(res, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()

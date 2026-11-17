"""Claude Editor <-> OpenFilm Studio (milestone 2): a Video Mania film as an editable OpenFilm timeline.

    vm openfilm setup                 install the image-bridge provider + the claude-editor skill into OpenFilm
    vm openfilm export <film>         <project>/openfilm/film.html + assets (every layer its own clip)
    vm openfilm open <film>           start Studio on it (prints the address; open it in the browser pane)
    vm openfilm render <film>         render the (possibly hand-edited) timeline -> renders/<film>_studio.mp4
    vm openfilm diff <film>           what the person changed in Studio since the export

Tracks, top first (film.html sections):
  1 effects   each editor-effect window: a muted trim of renders/<film>_fx.mp4 laid exactly over its moment
              (delete or trim it in Studio and that effect is gone)
  2 picture   one clip per chapter (shot), trims of the clean render renders/<film>.mp4
  3 voice     the voiceover
  4 music     one clip per song entrance: trims of audio/stems/music_bed.wav (exact levels and ducking)
  5 hook      one clip per hook sound, at its sync point (assets/sfx-hook)
  6 kit sfx   audio/stems/sfx_custom.wav (the kit's own sound effects)
Studio's render (`openfilm render --loudness=-14`) is then the delivery of the edited film.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
SKILL = S.parent
sys.path.insert(0, str(S))
import vm_env  # noqa: E402

OPSGEN = Path(os.environ.get("OPSGEN_BUILD", str(Path.home() / "video-production-workbench" / "opsgen")))
OPSGEN_CLI = OPSGEN / "packages" / "openfilm" / "bin" / "opsgen.mjs"
OF = ["node", str(OPSGEN_CLI)] if OPSGEN_CLI.exists() else ["npx", "-y", "openfilm@latest"]
SHARED = Path(os.environ.get("OPSGEN_SHARED_HOME", str(Path.home() / ".opsgen")))


def studio_env() -> dict:
    """the OpsGen Studio to talk to: the desktop app's (dev build: ~/.opsgen-dev) when it is running, else the web one"""
    home = os.environ.get("OPSGEN_HOME")
    if not home:
        dev = Path.home() / ".opsgen-dev"
        home = str(dev) if (dev / "run.json").exists() else str(SHARED)
    return dict(os.environ, OPSGEN_HOME=home, OPSGEN_NO_BROWSER="1")


def _run(cmd, cwd=None, check=True, timeout=None):
    exe = shutil.which(cmd[0]) or cmd[0]
    r = subprocess.run([exe, *map(str, cmd[1:])], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, env=studio_env())
    if check and r.returncode:
        raise SystemExit(f"FAILED: {' '.join(map(str, cmd[:4]))}\n{(r.stderr or r.stdout)[-2000:]}")
    return r


def put(src: Path, dst: Path):
    """copy unless dst is already the same file (Studio keeps open media locked on Windows)"""
    src, dst = Path(src), Path(dst)
    if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.stat().st_mtime >= src.stat().st_mtime:
        return
    try:
        shutil.copy2(src, dst)
    except PermissionError:
        print(f"(kept {dst.name}: open in Studio)", file=sys.stderr)


def setup() -> dict:
    """OpsGen: the image-bridge provider, the claude-editor skill, and the vm MCP server for every agent session"""
    home = SHARED / "providers" / "gpt-image-bridge"
    home.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SKILL / "templates" / "openfilm" / "providers" / "gpt-image-bridge" / "provider.mjs", home / "provider.mjs")
    sk = SKILL / "templates" / "openfilm" / "skill"
    r = _run([*OF, "skill", "add", sk], check=False, timeout=300)
    mcp = {"servers": [{"name": "vm", "command": str(vm_env.venv_python()), "args": [str(S / "vm.py"), "mcp"], "env": {}}]}
    (SHARED / "agent-mcp.json").write_text(json.dumps(mcp, indent=1), encoding="utf-8")
    return {"provider": str(home / "provider.mjs"), "agent_mcp": str(SHARED / "agent-mcp.json"),
            "skill_add": (r.stdout + r.stderr).strip()[-300:]}


def _cues(score: Path):
    """--cue file@offset:t0-t1[...] lines of a score.sh -> [(file, offset, t0, t1)]"""
    out = []
    if score.exists():
        for m in re.finditer(r"--cue\s+(\S+?)@([\d.]+):([\d.]+)-([\d.]+)", score.read_text(encoding="utf-8")):
            out.append((m[1], float(m[2]), float(m[3]), float(m[4])))
    return out


def _hook_sounds(cues_path: Path, film_lufs: float):
    import fx_pass
    man = {s["id"]: s for s in json.loads((SKILL / "assets" / "sfx-hook" / "manifest.json").read_text(encoding="utf-8"))}
    placed = []
    for c in json.loads(cues_path.read_text(encoding="utf-8"))["cues"]:
        p = fx_pass.PRESETS[c["fx"]]
        t0, t1, d = fx_pass.window(c)
        peak_t = t0 + (d / 2 if c.get("env", p["env"]) == "swell" else 0.0)
        sfx = c.get("sfx")
        if sfx is None:
            sfx = [{"id": a, "at": b, "gain_db": g} for a, b, g in p["sfx"]]
        for s in sfx:
            m = man.get(s["id"])
            if not m:
                continue
            anchor = {"start": t0, "peak": peak_t, "end": t1}[s.get("at", "start")]
            if p["centre"] == "around" and s.get("at", "peak") == "peak":
                anchor = c["t"]
            start = anchor - m["sync_at"]
            trim = max(0.0, -start)
            tier = {"hard": -2.0, "medium": -4.0, "soft": -7.0}.get(m.get("tier") or "medium", -4.0)
            gain_db = film_lufs + tier - (m.get("lufs") or -18.0) + s.get("gain_db", 0)
            placed.append(dict(id=s["id"], file=m["file"], at=max(0.0, start), trim=trim, dur=m["duration"],
                               volume=round(min(4.0, 10 ** (gain_db / 20)), 3), why=c.get("why", "")[:60]))
    return placed


def export(p: Path, captions: bool = False) -> dict:
    import brain
    import fx_pass
    od = p / "openfilm"
    (od / "assets").mkdir(parents=True, exist_ok=True)
    st = json.loads((p / "vm.json").read_text(encoding="utf-8")) if (p / "vm.json").exists() else {}
    S_ = brain.load_shots(str(p / "source" / "shots.js"))
    W, H = S_.get("size", [1920, 1080])
    film_len = float(S_.get("duration") or S_["shots"][-1]["t1"])
    film = p / "renders" / f"{p.name}.mp4"
    fx = p / "renders" / f"{p.name}_fx.mp4"
    A = od / "assets"
    if film.exists():
        put(film, A / "film.mp4")
    if fx.exists():
        put(fx, A / "film_fx.mp4")
    voice = p / st.get("voice", "input/vo.wav")
    put(voice, A / f"voice{voice.suffix}")
    vtt = p / "transcript" / "captions.vtt"
    # no subtitle track by default: the film's own kinetic type IS the captions (house rule 2026-10-22: nothing
    # outside the picture); captions=True copies the word times so Studio can make a caption track
    if captions and vtt.exists():
        put(vtt, A / "voice.vtt")
    elif (A / "voice.vtt").exists():
        (A / "voice.vtt").unlink()
    for stem in ("music_bed", "sfx_custom"):
        f = p / "audio" / "stems" / f"{stem}.wav"
        if f.exists():
            put(f, A / f"{stem}.wav")
    f2 = lambda x: f"{x:.3f}".rstrip("0").rstrip(".")
    tracks = {"effects": [], "picture": [], "voice": [], "music": [], "hook": [], "kitsfx": []}
    # picture: one clip per chapter
    for s in (S_["shots"] if film.exists() else []):
        tracks["picture"].append(f'<video id="shot-{s.get("id")}" src="assets/film.mp4#t={f2(s["t0"])},{f2(s["t1"])}" at="{f2(s["t0"])}" muted></video>')
    # effects: the fx render over each cue's window
    cues_path = p / "storyboard" / "fx_cues.json"
    hooks = []
    if fx.exists() and cues_path.exists():
        last = -1.0
        for n, c in enumerate(json.loads(cues_path.read_text(encoding="utf-8"))["cues"]):
            t0, t1, d = fx_pass.window(c)
            t0 = max(t0, last)          # clips on one track may not overlap
            if t1 - t0 < 0.05:
                continue
            tracks["effects"].append(f'<video id="fx-{n}-{c["fx"]}" src="assets/film_fx.mp4#t={f2(t0)},{f2(t1)}" at="{f2(t0)}" muted></video>')
            last = t1
        film_lufs = vm_env.loudness(fx).get("integrated_lufs", -14.0)
        hooks = _hook_sounds(cues_path, film_lufs)
    # voice
    tracks["voice"].append(f'<audio id="voice" src="assets/voice{voice.suffix}" at="0"></audio>')
    # music: one clip per entrance, trims of the phrased bed
    if (A / "music_bed.wav").exists():
        for i, (song, off, t0, t1) in enumerate(_cues(p / "audio" / "score.sh")):
            tracks["music"].append(f'<audio id="music-{i}-{Path(song).stem}" src="assets/music_bed.wav#t={f2(t0)},{f2(t1)}" at="{f2(t0)}"></audio>')
        if not tracks["music"]:
            tracks["music"].append('<audio id="music" src="assets/music_bed.wav" at="0"></audio>')
    # hook sounds: one clip each, on as many lanes as overlaps need
    lanes: list[list] = []
    (A / "sfx").mkdir(exist_ok=True)
    for h in sorted(hooks, key=lambda x: x["at"]):
        src = SKILL / "assets" / "sfx-hook" / h["file"]
        put(src, A / "sfx" / src.name)
        end = h["at"] + h["dur"] - h["trim"]
        for lane in lanes:
            if lane[-1][0] <= h["at"]:
                lane.append((end, h)); break
        else:
            lanes.append([(end, h)])
    hook_sections = []
    for li, lane in enumerate(lanes):
        clips = []
        for _, h in lane:
            end_in = min(h["dur"], h["trim"] + max(0.05, film_len - h["at"]))      # never past the film's end
            tt = f'#t={f2(h["trim"])},{f2(end_in)}'
            clips.append(f'<audio id="hook-{h["id"]}-{f2(h["at"])}" src="assets/sfx/{Path(h["file"]).name}{tt}" at="{f2(h["at"])}" volume="{h["volume"]}"></audio>')
        hook_sections.append(clips)
    if (A / "sfx_custom.wav").exists():
        tracks["kitsfx"].append('<audio id="kit-sfx" src="assets/sfx_custom.wav" at="0"></audio>')
    secs = [tracks["effects"], tracks["picture"], tracks["voice"], tracks["music"], *hook_sections, tracks["kitsfx"]]
    body = "\n".join("<section>\n  " + "\n  ".join(c) + "\n</section>" for c in secs if c)
    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={W}, height={H}">
<title>{p.name}</title>
<!-- Exported by Claude Editor (vm openfilm export). Tracks: effects / picture chapters / voice / music entrances / hook sounds / kit sfx. -->
</head>
<body>
{body}
</body>
</html>
"""
    (od / "film.html").write_text(html, encoding="utf-8")
    (od / ".vm-export.json").write_text(json.dumps({"film.html": html}), encoding="utf-8")
    return {"film": p.name, "folder": str(od), "tracks": {k: len(v) for k, v in tracks.items()} | {"hook_lanes": len(hook_sections)},
            "next": f"vm openfilm open {p.name}"}


def studio(p: Path) -> dict:
    """editor first: export, open in OpsGen, and mark the film live (every vm stage re-exports after it)"""
    st_file = p / "vm.json"
    st = json.loads(st_file.read_text(encoding="utf-8")) if st_file.exists() else {}
    st["studio"] = True
    st_file.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")
    ex = export(p)
    r = _run([*OF, "open", p / "openfilm"], check=False, timeout=120)
    url = next((l.split()[-1] for l in r.stdout.splitlines() if l.startswith("Studio")), None)
    return {**ex, "studio": url, "said": r.stdout.strip()[-300:], "home": studio_env()["OPSGEN_HOME"]}


def live(p: Path):
    """re-export after a stage when the film is open in OpsGen (vm studio)"""
    st_file = p / "vm.json"
    try:
        if json.loads(st_file.read_text(encoding="utf-8")).get("studio"):
            export(p)
    except Exception as ex:   # never break a stage over the live view
        print(f"(OpsGen live update skipped: {ex})", file=sys.stderr)


def open_(p: Path) -> dict:
    od = p / "openfilm"
    if not (od / "film.html").exists():
        export(p)
    exe = shutil.which("npx") or "npx"
    proc = subprocess.Popen([exe, "-y", "openfilm@latest", "open", str(od)], cwd=od, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
    url = None
    for _ in range(200):
        line = proc.stdout.readline()
        if not line:
            break
        m = re.search(r"https?://(?:localhost|127\.0\.0\.1)[:\d]*\S*", line)
        if m:
            url = m[0].rstrip(".,)")
            break
    return {"film": p.name, "studio": url, "pid": proc.pid, "note": "open the address in the browser pane; Studio keeps running"}


def render(p: Path) -> dict:
    od = p / "openfilm"
    r = _run([*OF, "render", "--loudness=-14"], cwd=od, timeout=7200, check=False)
    made = sorted(od.rglob("*.mp4"), key=lambda f: f.stat().st_mtime)
    made = [f for f in made if "assets" not in f.parts]
    if not made:
        raise SystemExit("OpenFilm render made no file:\n" + (r.stdout + r.stderr)[-1500:])
    dst = p / "renders" / f"{p.name}_studio.mp4"
    shutil.copy2(made[-1], dst)
    return {"film": p.name, "rendered": str(dst), "loudness": vm_env.loudness(dst)}


def diff(p: Path) -> dict:
    od = p / "openfilm"
    now = (od / "film.html").read_text(encoding="utf-8")
    was = json.loads((od / ".vm-export.json").read_text(encoding="utf-8"))["film.html"]
    clips = lambda h: {m[2]: m[1] for m in re.finditer(r'(<(?:video|audio|img|iframe)[^>]*id="([^"]+)"[^>]*>)', h)}
    a, b = clips(was), clips(now)
    return {"film": p.name, "removed": sorted(set(a) - set(b)), "added": sorted(set(b) - set(a)),
            "changed": sorted(k for k in set(a) & set(b) if a[k] != b[k])}


if __name__ == "__main__":
    print(__doc__)

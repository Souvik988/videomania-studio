"""vm: the command layer of Claude Editor (Video Mania). Every editing action is a command; the MCP server
(vm_mcp.py) and the editor's interface call the same commands. Add --json to any command for machine output.

    vm new <film> (--voice FILE | --script FILE) [--format 16:9|reel|9:16] [--recipe ID]
    vm status [<film>]                      stages, artifacts, gates, the next step
    vm hear [<film>]                        word times from the voiceover
    vm plan [<film>] --brief "..."          brain recall + ideas + recipe/preset suggestions
    vm research [<film>] --topic "..."      reference brief: local motion refs + the web queries to run
    vm assets [<film>] list|reuse|gen       asset pass (reuse the starter set, generate the rest with the image bridge)
    vm shots [<film>] --from-recipe ID      the recipe's shot list + a retime sheet for the new words
    vm check [<film>]                       every gate -> scorecard (brain, fx, hyperframes)
    vm look [<film>] --at 0.5,3,8           snapshots + contact sheet
    vm score [<film>]                       run audio/score.sh (or map the music)
    vm render [<film>] [--reel]             16:9 render, and the 4:5-in-9:16 reel
    vm fx [<film>] plan|check|apply         editor effects + hook sound (applies to the reel too)
    vm grade <in.mp4> --lut ID -o OUT       film-emulation LUT grade (296 looks)
    vm deliver [<film>]                     output/<film>/ with the srt and a report
    vm presets build|search "q"|show ID     one search over every preset (effects, sounds, LUTs, transitions, styles, recipes)
    vm recipe list|show ID|save <film> ID|use ID <film>
    vm brain sync|ask "q"|log <film>|vault  the director's memory (Obsidian vault + vectors)
    vm tl <film> / vm edit <film> '<ops>'   the OpsGen timeline in a few lines / edits as JSON operations
    vm media reverse|stabilize|denoise|key|reframe|track|beats|broll ...   footage edits (vm media -h)
    vm studio <film>                        EDITOR FIRST: open the film in OpsGen; every stage after it updates the timeline live
    vm openfilm setup|export|open|render|diff|studio [<film>]   the editable timeline in OpsGen
    vm doctor                               what this machine has
    vm mcp                                  serve every command as MCP tools over stdio

<film> may be omitted when the current folder is inside a project. Projects live in
<workbench>/OpenMontage/projects/<film>/.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent            # skill scripts
SKILL = S.parent
sys.path.insert(0, str(S))
import vm_env  # noqa: E402

HF = f"hyperframes@{vm_env.HF_VERSION}"
OUTPUT_ROOT = Path(os.environ.get("VM_OUTPUT", str(Path.home() / "OneDrive" / "Desktop" / "video editor" / "output")))
JSON_OUT = False


# ------------------------------------------------------------------------------------------------ basics
def py() -> str:
    return str(vm_env.venv_python())


def projects_root() -> Path:
    return vm_env.workbench() / "OpenMontage" / "projects"


def resolve(film: str | None) -> Path:
    if film:
        p = Path(film)
        if p.is_dir() and ((p / "vm.json").exists() or (p / "source").is_dir()):
            return p.resolve()
        q = projects_root() / film
        if q.is_dir():
            return q
        raise SystemExit(f"no film '{film}' (looked in {projects_root()})")
    cwd = Path.cwd().resolve()
    for c in [cwd, *cwd.parents]:
        if (c / "vm.json").exists():
            return c
    raise SystemExit("which film? pass <film> or run inside a project folder")


def state(p: Path) -> dict:
    f = p / "vm.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"film": p.name, "stages": {}}


def save_state(p: Path, st: dict):
    (p / "vm.json").write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def mark(p: Path, stage: str, **info):
    st = state(p)
    st.setdefault("stages", {})[stage] = {"at": dt.datetime.now().isoformat(timespec="seconds"), **info}
    save_state(p, st)
    if st.get("studio") and stage in ("hear", "score", "render", "fx"):
        import vm_openfilm
        vm_openfilm.live(p)          # the person watches the timeline fill in, in OpsGen


def run(cmd: list, cwd=None, check=True, timeout=None, quiet=False) -> subprocess.CompletedProcess:
    exe = shutil.which(str(cmd[0])) or str(cmd[0])
    r = subprocess.run([exe, *map(str, cmd[1:])], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=timeout)
    if not quiet and not JSON_OUT:
        out = (r.stdout or "")[-4000:]
        if out.strip():
            print(out.rstrip())
    if check and r.returncode != 0:
        raise SystemExit(f"FAILED ({r.returncode}): {' '.join(map(str, cmd[:5]))}\n{(r.stderr or r.stdout)[-2500:]}")
    return r


def out(data: dict):
    if JSON_OUT:
        print(json.dumps(data, indent=1, ensure_ascii=False, default=str))
    else:
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                print(f"{k}: {json.dumps(v, ensure_ascii=False, default=str)[:600]}")
            else:
                print(f"{k}: {v}")


def media_len(path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], quiet=True)
    return float(r.stdout.strip())


def renders(p: Path) -> list[Path]:
    return sorted((p / "renders").glob("*.mp4"), key=lambda f: f.stat().st_mtime) if (p / "renders").exists() else []


# ------------------------------------------------------------------------------------------------ new / status
def cmd_new(a):
    p = projects_root() / a.film
    if (p / "vm.json").exists() and not a.force:
        raise SystemExit(f"{p} already exists (use --force to reset its state)")
    (p / "input").mkdir(parents=True, exist_ok=True)
    voice = None
    if a.voice:
        src = Path(a.voice)
        voice = p / "input" / src.name
        shutil.copy2(src, voice)
    elif a.script:
        txt = p / "input" / "script.txt"
        shutil.copy2(a.script, txt) if Path(a.script).exists() else txt.write_text(a.script, encoding="utf-8")
        voice = p / "input" / "vo.wav"
        run(["npx", "-y", HF, "tts", txt, "-o", voice], timeout=600)
    else:
        raise SystemExit("give --voice <file> or --script <file or text>")
    dur = round(media_len(voice) + 0.02, 2)
    size = {"16:9": "1920x1080", "reel": "1920x1080", "9:16": "1080x1920"}[a.format]
    run([py(), S / "new_film.py", p, "--duration", dur, "--size", size], check=True)
    st = {"film": a.film, "created": dt.datetime.now().isoformat(timespec="seconds"), "voice": str(voice.relative_to(p)),
          "duration": dur, "format": a.format, "recipe": a.recipe, "stages": {"new": {"at": dt.datetime.now().isoformat(timespec="seconds")}}}
    save_state(p, st)
    out({"film": a.film, "project": str(p), "voice": str(voice), "duration": dur, "format": a.format,
         "next": f"vm hear {a.film}"})


STAGES = [
    ("hear", "word times", lambda p: (p / "transcript" / "words.json").exists(), "vm hear"),
    ("plan", "brain ideas", lambda p: (p / "brief" / "ideas_seed.md").exists() or (p / "brief" / "ideas.md").exists(), "vm plan --brief \"...\""),
    ("assets", "asset pass", lambda p: (p / "source" / "assets" / "mascot" / "me" / "poses.json").exists(), "vm assets reuse | gen"),
    ("shots", "shot list written", lambda p: (p / "source" / "shots.js").exists() and "window.SHOTS" in (p / "source" / "shots.js").read_text(encoding="utf-8")
     and "shots: [\n    // {" not in (p / "source" / "shots.js").read_text(encoding="utf-8"), "write source/shots.js (vm shots --from-recipe ID helps)"),
    ("check", "gates pass", lambda p: state(p).get("stages", {}).get("check", {}).get("pass") is True, "vm check"),
    ("score", "sound mixed", lambda p: (p / "source" / "mix.wav").exists(), "vm score"),
    ("render", "film rendered", lambda p: any(not f.stem.endswith(("_fx", "_4x5", "_9x16")) for f in renders(p)), "vm render [--reel]"),
    ("fx", "editor effects + hook", lambda p: any(f.stem.endswith("_fx") or "_fx_" in f.stem for f in renders(p)), "vm fx plan; vm fx check; vm fx apply"),
    ("deliver", "delivered", lambda p: (OUTPUT_ROOT / p.name).exists(), "vm deliver"),
]


def cmd_status(a):
    p = resolve(a.film)
    st = state(p)
    rows, nxt = [], None
    for key, what, done, how in STAGES:
        ok = bool(done(p))
        rows.append({"stage": key, "what": what, "done": ok})
        if not ok and not nxt:
            nxt = how
    out({"film": p.name, "project": str(p), "duration": st.get("duration"), "format": st.get("format"),
         "recipe": st.get("recipe"), "stages": rows, "renders": [f.name for f in renders(p)],
         "scorecard": st.get("stages", {}).get("check", {}).get("gates"), "next": nxt or "done"})


# ------------------------------------------------------------------------------------------------ hear / plan / research
def cmd_hear(a):
    p = resolve(a.film)
    st = state(p)
    voice = p / st["voice"]
    run([py(), S / "ingest.py", "--project", p.name, "--audio", voice, "--language", a.language], timeout=1800)
    words = json.loads((p / "transcript" / "words.json").read_text(encoding="utf-8"))
    words = words.get("words", words)
    text = " ".join(w.get("word", w.get("text", "")) for w in words)
    mark(p, "hear", words=len(words))
    out({"film": p.name, "words": len(words), "text": text[:1500], "file": str(p / "transcript" / "words.json"), "next": "vm plan --brief \"...\""})


def cmd_plan(a):
    p = resolve(a.film)
    (p / "brief").mkdir(exist_ok=True)
    rec = run([py(), S / "brain.py", "recall", "--brief", a.brief], quiet=True, check=False)
    ide = run([py(), S / "brain.py", "ideas", "--brief", a.brief, "--project", p], quiet=True, check=False)
    import vm_presets
    sugg = vm_presets.search(a.brief, k=12)
    (p / "brief" / "recall.md").write_text(rec.stdout, encoding="utf-8")
    mark(p, "plan", brief=a.brief)
    out({"film": p.name, "recall": rec.stdout[-1500:], "ideas_file": str(p / "brief" / "ideas_seed.md"),
         "ideas": ide.stdout[:2500], "presets": [f"{r['id']} — {r['name']}" for r in sugg],
         "next": "write brief/ideas.md (five concepts), then vm assets / vm shots"})


def cmd_research(a):
    p = resolve(a.film)
    (p / "brief").mkdir(exist_ok=True)
    loc = run([py(), S / "motion_refs.py", "--query", a.topic], quiet=True, check=False)
    queries = [f"{a.topic} motion design reel", f"{a.topic} kinetic typography", f"{a.topic} 3D explainer animation",
               f"site:pinterest.com {a.topic} motion graphics", f"site:behance.net {a.topic} motion design"]
    md = [f"# Research: {a.topic}", "", "## Local references (703 Opus prompts, motion_refs.py)", "", loc.stdout[:3000], "",
          "## Web (run these with firecrawl_search / the browser; Pinterest: browse, take ideas only, never the images)", ""]
    md += [f"- [ ] `{q}`" for q in queries]
    md += ["", "## Decoded references", "", "For each video reference: `analyze_video.py <ref> --out qa/reference` and note 1 technique.", ""]
    f = p / "brief" / "research.md"
    f.write_text("\n".join(md), encoding="utf-8")
    mark(p, "research", topic=a.topic)
    out({"film": p.name, "file": str(f), "web_queries": queries})


# ------------------------------------------------------------------------------------------------ assets
GEN = Path.home() / ".claude" / "skills" / "gpt-image-bridge" / "bin" / "gpt-image-2"


def cmd_assets(a):
    p = resolve(a.film)
    src = p / "source" / "assets"
    man = p / "storyboard" / "assets.json"
    if a.action == "reuse":
        starter = SKILL / "assets" / "voxel-starter"
        for rel in ("mascot/me", "gen", "plates", "cast"):
            if (starter / rel).exists():
                shutil.copytree(starter / rel, src / rel, dirs_exist_ok=True)
        mark(p, "assets", reused=True)
        out({"film": p.name, "reused": str(starter), "next": "list what is still missing in storyboard/assets.json, then vm assets gen"})
        return
    rows = json.loads(man.read_text(encoding="utf-8")) if man.exists() else []
    if a.action == "list":
        for r in rows:
            r["exists"] = (p / "source" / r.get("file", "")).exists() if r.get("file") else False
        out({"film": p.name, "manifest": str(man), "assets": rows,
             "how": 'rows: {"id","source":"gen|footage|photo|code","prompt","file":"assets/gen/x.png","size":"1536x1024","ref":["photo.png"]}'})
        return
    # gen: every gen row whose file is missing, 3 at a time
    todo = [r for r in rows if r.get("source") == "gen" and r.get("file") and not (p / "source" / r["file"]).exists()]
    if not todo:
        out({"film": p.name, "generated": 0, "note": "nothing to generate (all gen rows exist)"})
        return
    procs, done = [], []
    bash = shutil.which("bash") or "bash"
    for r in todo:
        dst = p / "source" / r["file"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        if r.get("ref"):
            cmd = [bash, str(S / "gpt_image_ref.sh"), r["prompt"], str(dst)]
            for ref in r["ref"]:
                cmd += ["--ref", str((p / ref) if not Path(ref).is_absolute() else ref)]
            cmd += ["--size", r.get("size", "1536x1024")]
        else:
            cmd = [bash, str(GEN), r["prompt"], str(dst), "--size", r.get("size", "1536x1024")]
        procs.append((r, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
        while len([x for x in procs if x[1].poll() is None]) >= 3:
            procs[0][1].wait(timeout=900)
    for r, pr in procs:
        pr.wait(timeout=900)
        done.append({"id": r["id"], "ok": (p / "source" / r["file"]).exists()})
    mark(p, "assets", generated=done)
    out({"film": p.name, "generated": done, "next": "open every picture and look at it before using it"})


# ------------------------------------------------------------------------------------------------ shots from recipe
def cmd_shots(a):
    p = resolve(a.film)
    import vm_recipes
    r = vm_recipes.get(a.from_recipe)
    shots_src = vm_recipes.file(r, "shots")
    dst = p / "source" / "shots.recipe.js"
    shutil.copy2(shots_src, dst)
    sys.path.insert(0, str(S))
    import brain
    S_ = brain.load_shots(str(shots_src))
    words = json.loads((p / "transcript" / "words.json").read_text(encoding="utf-8")) if (p / "transcript" / "words.json").exists() else []
    words = words.get("words", words) if isinstance(words, dict) else words
    lines = ["# Retime sheet", "", f"Recipe `{r['id']}` ({S_.get('duration')} s) -> this voiceover ({state(p).get('duration')} s).",
             "Keep the recipe's structure, devices and moves; put every time on THIS voiceover's words.", "",
             "| shot | recipe t0-t1 | set | why |", "|---|---|---|---|"]
    for s in S_["shots"]:
        lines.append(f"| {s.get('id')} | {s.get('t0')}-{s.get('t1')} | {s.get('set')} | {str(s.get('why', ''))[:90]} |")
    lines += ["", "## This voiceover's words", "", " ".join(f"{w.get('word', w.get('text'))}@{w['start']:.2f}" for w in words)]
    (p / "storyboard").mkdir(exist_ok=True)
    (p / "storyboard" / "retime.md").write_text("\n".join(lines), encoding="utf-8")
    out({"film": p.name, "recipe_shots": str(dst), "retime_sheet": str(p / "storyboard" / "retime.md"),
         "next": "write source/shots.js from the recipe on the new word times, then vm check"})


# ------------------------------------------------------------------------------------------------ check / look
def cmd_check(a):
    p = resolve(a.film)
    gates = {}
    shots = p / "source" / "shots.js"
    if shots.exists():
        r = run([py(), S / "brain.py", "check", shots, "--project", p], quiet=True, check=False)
        (p / "brief").mkdir(exist_ok=True)
        (p / "brief" / "brain_check.txt").write_text(r.stdout, encoding="utf-8")
        gates["brain"] = {"pass": r.returncode == 0, "fails": [l for l in r.stdout.splitlines() if l.startswith("FAIL")],
                          "warns": [l for l in r.stdout.splitlines() if l.startswith("WARN")]}
    cues = p / "storyboard" / "fx_cues.json"
    if cues.exists():
        r = run([py(), S / "fx_pass.py", "check", cues], quiet=True, check=False)
        gates["fx"] = {"pass": r.returncode == 0, "lines": r.stdout.strip().splitlines()}
    if (p / "source" / "index.html").exists() and not a.fast:
        r = run(["npx", "-y", HF, "check"], cwd=p / "source", quiet=True, check=False, timeout=600)
        txt = r.stdout + r.stderr
        errs = [l.strip() for l in txt.splitlines() if l.strip().startswith("✗")]
        known = [e for e in errs if "f_d.jpg" in e]          # known false alarm of the frame preloader
        gates["hyperframes"] = {"pass": len(errs) == len(known), "errors": errs, "ignored_known": known}
    ok = all(g["pass"] for g in gates.values()) if gates else False
    mark(p, "check", gates=gates, **{"pass": ok})
    out({"film": p.name, "pass": ok, "gates": gates})


def cmd_look(a):
    p = resolve(a.film)
    o = p / f"snaps_{dt.datetime.now().strftime('%H%M%S')}"
    run(["npx", "-y", HF, "snapshot", "--at", a.at, "--no-end", "--describe", "false", "-o", o], cwd=p / "source", timeout=900, quiet=True)
    sheets = sorted(str(f) for f in o.glob("contact-sheet*.jpg"))
    out({"film": p.name, "dir": str(o), "contact_sheets": sheets, "frames": sorted(str(f) for f in o.glob("frame-*.png"))})


# ------------------------------------------------------------------------------------------------ score / render / fx
def cmd_score(a):
    p = resolve(a.film)
    st = state(p)
    sc = p / "audio" / "score.sh"
    if sc.exists():
        env = dict(os.environ, S=str(S), P=str(p), VOICE=st["voice"], PY=py())
        r = subprocess.run([shutil.which("bash") or "bash", str(sc)], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            raise SystemExit(r.stderr[-2000:] or r.stdout[-2000:])
        spread = [l for l in r.stdout.splitlines() if "momentary" in l]
        mark(p, "score", spread=spread)
        out({"film": p.name, "mix": str(p / "source" / "mix.wav"), "spread": spread})
    else:
        songs = sorted((p / "audio").glob("music*/*.mp3")) if (p / "audio").exists() else []
        if songs:
            run([py(), S / "music_map.py", *songs, "-o", p / "audio" / "music_map.json"], quiet=True)
        out({"film": p.name, "note": "no audio/score.sh yet", "music_map": str(p / "audio" / "music_map.json") if songs else None,
             "how": "copy templates/voxel-diorama/examples/director-film-v5.score.sh to audio/score.sh, cast songs by meaning, run vm score"})


def cmd_render(a):
    p = resolve(a.film)
    o = p / "renders"
    o.mkdir(exist_ok=True)
    made = []
    if not a.reel_only:
        f = o / f"{p.name}.mp4"
        run(["npx", "-y", HF, "render", "-o", f], cwd=p / "source", timeout=3600, quiet=True)
        made.append(str(f))
    if a.reel or a.reel_only:
        run([py(), S / "reel_frame.py", "prep", p / "source", "--size", "1080x1350", "--keep", "0.82"], quiet=True)
        try:
            f4 = o / f"{p.name}_4x5.mp4"
            run(["npx", "-y", HF, "render", "-o", f4], cwd=p / "source", timeout=3600, quiet=True)
            made.append(str(f4))
        finally:
            run([py(), S / "reel_frame.py", "restore", p / "source"], quiet=True)
    mark(p, "render", files=made)
    out({"film": p.name, "rendered": made, "next": "vm fx plan; vm fx check; vm fx apply"})


def cmd_fx(a):
    p = resolve(a.film)
    cues = p / "storyboard" / "fx_cues.json"
    if a.action == "plan":
        run([py(), S / "fx_pass.py", "plan", p, "--hook", a.hook], quiet=True)
        out({"film": p.name, "cues": json.loads(cues.read_text(encoding="utf-8"))["cues"], "file": str(cues),
             "next": "read it, swap what does not fit, then vm fx check"})
    elif a.action == "check":
        r = run([py(), S / "fx_pass.py", "check", cues], quiet=True, check=False)
        out({"film": p.name, "pass": r.returncode == 0, "lines": r.stdout.strip().splitlines()})
    else:
        made = []
        main = p / "renders" / f"{p.name}.mp4"
        if main.exists():
            f = p / "renders" / f"{p.name}_fx.mp4"
            run([py(), S / "fx_pass.py", "apply", main, cues, "-o", f], quiet=True)
            made.append(str(f))
        m4 = p / "renders" / f"{p.name}_4x5.mp4"
        if m4.exists():
            f4 = p / "renders" / f"{p.name}_fx_4x5.mp4"
            run([py(), S / "fx_pass.py", "apply", m4, cues, "-o", f4], quiet=True)
            reel = p / "renders" / f"{p.name}_fx_reel_9x16.mp4"
            run([py(), S / "reel_frame.py", "pad", f4, reel], quiet=True)
            made.append(str(reel))
        loud = {Path(f).name: vm_env.loudness(f) for f in made}
        mark(p, "fx", files=made, loudness=loud)
        out({"film": p.name, "made": made, "loudness": loud, "next": "look at frame 0 and every cue, then vm deliver"})


def cmd_grade(a):
    import vm_presets
    lut = vm_presets.lut_path(a.lut)
    vf = f"lut3d=file='{lut.as_posix().replace(':', chr(92) + ':')}':interp=tetrahedral"
    if a.mix < 1:
        vf = f"split[a][b];[b]{vf}[g];[a][g]blend=all_expr='A*(1-{a.mix})+B*{a.mix}'"
    run(["ffmpeg", "-v", "error", "-y", "-i", a.inp, "-vf", vf, "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "copy", a.o])
    out({"graded": a.o, "lut": str(lut), "mix": a.mix})


# ------------------------------------------------------------------------------------------------ deliver
def cmd_deliver(a):
    p = resolve(a.film)
    d = OUTPUT_ROOT / p.name
    d.mkdir(parents=True, exist_ok=True)
    pick = [f for f in renders(p) if "_fx" in f.stem] or [f for f in renders(p) if not f.stem.endswith("_4x5")]
    files = []
    for f in pick:
        if f.stem.endswith("_fx_4x5"):
            continue
        shutil.copy2(f, d / f.name)
        files.append(str(d / f.name))
    srt = p / "transcript" / "captions.srt"
    if srt.exists():
        shutil.copy2(srt, d / f"{p.name}.srt")
    for extra in ("source/shots.js", "audio/score.sh", "storyboard/fx_cues.json"):
        if (p / extra).exists():
            shutil.copy2(p / extra, d / f"{p.name}.{Path(extra).name}")
    report = {"film": p.name, "files": files, "loudness": {Path(f).name: vm_env.loudness(f) for f in files},
              "gates": state(p).get("stages", {}).get("check", {}).get("gates"),
              "note": "sound is measured, not heard; songs in the film may be for private viewing only"}
    (d / "report.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    mark(p, "deliver", dir=str(d))
    out({**report, "dir": str(d), "next": f"vm brain log {p.name} (after the user's verdict add --verdict)"})


# ------------------------------------------------------------------------------------------------ presets / recipes / brain / doctor
def cmd_presets(a):
    import vm_presets
    if a.action == "build":
        n = vm_presets.build()
        out({"indexed": n})
    elif a.action == "search":
        rows = vm_presets.search(a.query, k=a.k, kinds=set(a.kind.split(",")) if a.kind else None)
        out({"query": a.query, "results": rows})
    elif a.action == "kinds":
        out(vm_presets.kinds())
    else:
        out(vm_presets.show(a.query))


def cmd_recipe(a):
    import vm_recipes
    if a.action == "list":
        out({"recipes": vm_recipes.listing()})
    elif a.action == "show":
        out(vm_recipes.get(a.args[0]))
    elif a.action == "save":
        p = resolve(a.args[0])
        out(vm_recipes.save(p, a.args[1], a.title or a.args[1], a.about or ""))
    elif a.action == "use":
        p = resolve(a.args[1])
        out(vm_recipes.use(a.args[0], p))


def cmd_brain(a):
    import vm_brain
    if a.action == "sync":
        out(vm_brain.sync())
    elif a.action == "ask":
        out({"query": a.text, "notes": vm_brain.ask(a.text, k=a.k)})
    elif a.action == "log":
        p = resolve(a.text)
        out(vm_brain.log_film(p, verdict=a.verdict, good=a.good, bad=a.bad))
    else:
        out({"vault": str(vm_brain.vault()), "open_in": "Obsidian -> Open folder as vault"})


def cmd_doctor(a):
    chk = {}
    for tool in ("ffmpeg", "ffprobe", "node", "npx", "bash", "claude", "codex"):
        chk[tool] = bool(shutil.which(tool))
    chk["workbench"] = str(vm_env.workbench())
    chk["image_bridge"] = GEN.exists()
    chk["sharp_3d"] = (vm_env.workbench() / "tools" / "ml-sharp" / ".venv" / "Scripts" / "sharp.exe").exists()
    chk["effectcraft"] = any((vm_env.workbench() / "research" / "effectcraft-bin").rglob("effectcraft-cli.exe")) if (vm_env.workbench() / "research" / "effectcraft-bin").exists() else False
    chk["openfilm"] = "npx -y openfilm@latest (Studio)"
    du = shutil.disk_usage(str(vm_env.workbench()))
    chk["disk_free_gb"] = round(du.free / 1e9, 1)
    out(chk)


def cmd_openfilm(a):
    import vm_openfilm as of
    if a.action == "setup":
        out(of.setup())
        return
    p = resolve(a.film)
    out({"export": of.export, "open": of.open_, "render": of.render, "diff": of.diff, "studio": of.studio}[a.action](p))


def cmd_tl(a):
    import vm_openfilm as of
    p = resolve(a.film)
    r = of._run([*of.OF, "tl", "--film", p / "openfilm"] + (["--json"] if JSON_OUT else []), check=False, timeout=120)
    print((r.stdout or r.stderr).strip())


def cmd_edit(a):
    import vm_openfilm as of
    p = resolve(a.film)
    r = of._run([*of.OF, "edit", a.ops, "--film", p / "openfilm"] + (["--dry"] if a.dry else []), check=False, timeout=300)
    print((r.stdout or r.stderr).strip())
    if r.returncode:
        raise SystemExit(1)


def cmd_media(a):
    import vm_media
    vm_media.main(a.rest)


def cmd_mcp(a):
    import vm_mcp
    vm_mcp.serve()


# ------------------------------------------------------------------------------------------------ main
def main(argv=None):
    global JSON_OUT
    for stream in (sys.stdout, sys.stderr):      # Windows consoles default to cp1252; notes hold ≤, →, emoji
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    raw = list(sys.argv[1:] if argv is None else argv)
    rest = [x for x in raw if x != "--json"]
    if rest[:1] == ["media"]:                    # footage edits have their own options (vm media -h)
        import vm_media
        vm_media.main(rest[1:])
        return
    ap = argparse.ArgumentParser(prog="vm", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sp = ap.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("new"); x.add_argument("film"); x.add_argument("--voice"); x.add_argument("--script"); x.add_argument("--format", default="reel", choices=["16:9", "reel", "9:16"]); x.add_argument("--recipe"); x.add_argument("--force", action="store_true"); x.set_defaults(fn=cmd_new)
    x = sp.add_parser("status"); x.add_argument("film", nargs="?"); x.set_defaults(fn=cmd_status)
    x = sp.add_parser("hear"); x.add_argument("film", nargs="?"); x.add_argument("--language", default="en"); x.set_defaults(fn=cmd_hear)
    x = sp.add_parser("plan"); x.add_argument("film", nargs="?"); x.add_argument("--brief", required=True); x.set_defaults(fn=cmd_plan)
    x = sp.add_parser("research"); x.add_argument("film", nargs="?"); x.add_argument("--topic", required=True); x.set_defaults(fn=cmd_research)
    x = sp.add_parser("assets"); x.add_argument("action", choices=["list", "reuse", "gen"]); x.add_argument("film", nargs="?"); x.set_defaults(fn=cmd_assets)
    x = sp.add_parser("shots"); x.add_argument("film", nargs="?"); x.add_argument("--from-recipe", required=True); x.set_defaults(fn=cmd_shots)
    x = sp.add_parser("check"); x.add_argument("film", nargs="?"); x.add_argument("--fast", action="store_true", help="skip the hyperframes check"); x.set_defaults(fn=cmd_check)
    x = sp.add_parser("look"); x.add_argument("film", nargs="?"); x.add_argument("--at", default="0.2,1,3"); x.set_defaults(fn=cmd_look)
    x = sp.add_parser("score"); x.add_argument("film", nargs="?"); x.set_defaults(fn=cmd_score)
    x = sp.add_parser("render"); x.add_argument("film", nargs="?"); x.add_argument("--reel", action="store_true"); x.add_argument("--reel-only", action="store_true"); x.set_defaults(fn=cmd_render)
    x = sp.add_parser("fx"); x.add_argument("action", choices=["plan", "check", "apply"]); x.add_argument("film", nargs="?"); x.add_argument("--hook", default="warp"); x.set_defaults(fn=cmd_fx)
    x = sp.add_parser("grade"); x.add_argument("inp"); x.add_argument("--lut", required=True); x.add_argument("-o", required=True); x.add_argument("--mix", type=float, default=1.0); x.set_defaults(fn=cmd_grade)
    x = sp.add_parser("deliver"); x.add_argument("film", nargs="?"); x.set_defaults(fn=cmd_deliver)
    x = sp.add_parser("presets"); x.add_argument("action", choices=["build", "search", "show", "kinds"]); x.add_argument("query", nargs="?", default=""); x.add_argument("-k", type=int, default=12); x.add_argument("--kind"); x.set_defaults(fn=cmd_presets)
    x = sp.add_parser("recipe"); x.add_argument("action", choices=["list", "show", "save", "use"]); x.add_argument("args", nargs="*"); x.add_argument("--title"); x.add_argument("--about"); x.set_defaults(fn=cmd_recipe)
    x = sp.add_parser("brain"); x.add_argument("action", choices=["sync", "ask", "log", "vault"]); x.add_argument("text", nargs="?", default=""); x.add_argument("-k", type=int, default=8); x.add_argument("--verdict"); x.add_argument("--good", action="store_true"); x.add_argument("--bad", action="store_true"); x.set_defaults(fn=cmd_brain)
    x = sp.add_parser("openfilm"); x.add_argument("action", choices=["setup", "export", "open", "render", "diff", "studio"]); x.add_argument("film", nargs="?"); x.set_defaults(fn=cmd_openfilm)
    x = sp.add_parser("studio"); x.add_argument("film", nargs="?"); x.set_defaults(fn=lambda a: cmd_openfilm(argparse.Namespace(action="studio", film=a.film)))
    x = sp.add_parser("tl"); x.add_argument("film", nargs="?"); x.set_defaults(fn=cmd_tl)
    x = sp.add_parser("edit"); x.add_argument("film"); x.add_argument("ops"); x.add_argument("--dry", action="store_true"); x.set_defaults(fn=cmd_edit)
    x = sp.add_parser("media", add_help=False); x.add_argument("rest", nargs=argparse.REMAINDER); x.set_defaults(fn=cmd_media)
    x = sp.add_parser("doctor"); x.set_defaults(fn=cmd_doctor)
    x = sp.add_parser("mcp"); x.set_defaults(fn=cmd_mcp)
    a = ap.parse_args(argv)
    JSON_OUT = a.json
    a.fn(a)


if __name__ == "__main__":
    main()

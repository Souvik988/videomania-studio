"""MCP server for Claude Editor: every `vm` command as a tool, over stdio (JSON-RPC 2.0, one message per line).

    python vm.py mcp            (or: python vm_mcp.py)
Register in a project with .mcp.json:
    {"mcpServers": {"vm": {"command": "<workbench venv python>", "args": ["<skill>/scripts/vm.py", "mcp"]}}}

Each tool runs `vm --json <command>` in a child process, so a crash in one command never kills the server, and
returns its JSON. Long renders can outlast a client's tool timeout: for those, run `vm render` in a terminal.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

S = Path(__file__).resolve().parent
PROTOCOL = "2025-06-18"

F = {"type": "string", "description": "film id (folder under OpenMontage/projects)"}
TOOLS = [
    ("vm_status", "Where a film stands: stages done, renders, gates, the next step.", {"film": F}, ["film"], lambda a: ["status", a["film"]]),
    ("vm_new", "Start a film from a voiceover file or a script (local TTS). Format: 16:9, reel (4:5 in 9:16) or 9:16.",
     {"film": F, "voice": {"type": "string"}, "script": {"type": "string"}, "format": {"type": "string", "enum": ["16:9", "reel", "9:16"]}, "recipe": {"type": "string"}},
     ["film"], lambda a: ["new", a["film"]] + (["--voice", a["voice"]] if a.get("voice") else []) + (["--script", a["script"]] if a.get("script") else [])
     + (["--format", a["format"]] if a.get("format") else []) + (["--recipe", a["recipe"]] if a.get("recipe") else [])),
    ("vm_hear", "Word times from the voiceover (faster-whisper, local).", {"film": F, "language": {"type": "string"}}, ["film"],
     lambda a: ["hear", a["film"], "--language", a.get("language", "en")]),
    ("vm_plan", "Director's brain: recall past films, constraint card, Pocket draws, preset suggestions.", {"film": F, "brief": {"type": "string"}}, ["film", "brief"],
     lambda a: ["plan", a["film"], "--brief", a["brief"]]),
    ("vm_research", "Reference brief: local Opus motion references + the web/Pinterest queries to run.", {"film": F, "topic": {"type": "string"}}, ["film", "topic"],
     lambda a: ["research", a["film"], "--topic", a["topic"]]),
    ("vm_assets", "Asset pass: list storyboard/assets.json, reuse the starter set, or generate missing pictures with the ChatGPT image bridge (3 at a time).",
     {"film": F, "action": {"type": "string", "enum": ["list", "reuse", "gen"]}}, ["film", "action"], lambda a: ["assets", a["action"], a["film"]]),
    ("vm_shots_from_recipe", "Copy a recipe's shot list into the film and write a retime sheet for the new words.", {"film": F, "recipe": {"type": "string"}}, ["film", "recipe"],
     lambda a: ["shots", a["film"], "--from-recipe", a["recipe"]]),
    ("vm_check", "Run every gate (brain: rhythm/novelty/asset-first/why; fx: hook/flash/density; hyperframes) and return the scorecard.",
     {"film": F, "fast": {"type": "boolean"}}, ["film"], lambda a: ["check", a["film"]] + (["--fast"] if a.get("fast") else [])),
    ("vm_look", "Snapshots at given seconds + a contact sheet (read the image files it returns).", {"film": F, "at": {"type": "string", "description": "e.g. 0.2,1,3.5"}}, ["film"],
     lambda a: ["look", a["film"], "--at", a.get("at", "0.2,1,3")]),
    ("vm_score", "Mix the sound: run audio/score.sh (songs cast by meaning) -> source/mix.wav with the measured spread.", {"film": F}, ["film"], lambda a: ["score", a["film"]]),
    ("vm_render", "Render the film (16:9) and/or the reel (4:5, padded later). Slow: minutes per 10 s.", {"film": F, "reel": {"type": "boolean"}, "reel_only": {"type": "boolean"}}, ["film"],
     lambda a: ["render", a["film"]] + (["--reel"] if a.get("reel") else []) + (["--reel-only"] if a.get("reel_only") else [])),
    ("vm_fx", "Editor effects + hook sound: plan (from the shot list), check (gates), apply (to the render and the reel).",
     {"film": F, "action": {"type": "string", "enum": ["plan", "check", "apply"]}, "hook": {"type": "string", "enum": ["warp", "glitch", "shock", "flashzoom"]}}, ["film", "action"],
     lambda a: ["fx", a["action"], a["film"], "--hook", a.get("hook", "warp")]),
    ("vm_grade", "Film-emulation colour grade with a LUT (vm_presets_search kind=grade).", {"input": {"type": "string"}, "lut": {"type": "string"}, "output": {"type": "string"}, "mix": {"type": "number"}},
     ["input", "lut", "output"], lambda a: ["grade", a["input"], "--lut", a["lut"], "-o", a["output"], "--mix", str(a.get("mix", 1.0))]),
    ("vm_deliver", "Copy the finished film(s), captions, shot list, score and fx cues to output/<film>/ with a measured report.", {"film": F}, ["film"], lambda a: ["deliver", a["film"]]),
    ("vm_presets_search", "Search EVERY preset by meaning and keywords: effects, hook sounds, 296 film LUTs, 238 GL transitions, 308 After-Effects-equivalent effects, WebGPU nodes, recipes, and the Pocket's 10,625 styles/moves/moments.",
     {"query": {"type": "string"}, "kind": {"type": "string", "description": "effect,sound,grade,transition,ae-effect,node,recipe (comma list)"}, "k": {"type": "integer"}}, ["query"],
     lambda a: ["presets", "search", a["query"], "-k", str(a.get("k", 12))] + (["--kind", a["kind"]] if a.get("kind") else [])),
    ("vm_preset_show", "One preset in full, with how to use it.", {"id": {"type": "string"}}, ["id"], lambda a: ["presets", "show", a["id"]]),
    ("vm_recipe", "Whole-film presets: list, show <id>, save <film> <id>, use <id> <film>.", {"action": {"type": "string", "enum": ["list", "show", "save", "use"]},
     "args": {"type": "array", "items": {"type": "string"}}, "title": {"type": "string"}, "about": {"type": "string"}}, ["action"],
     lambda a: ["recipe", a["action"], *a.get("args", [])] + (["--title", a["title"]] if a.get("title") else []) + (["--about", a["about"]] if a.get("about") else [])),
    ("vm_brain_ask", "Ask the director's memory (lessons, the user's own notes, past films, effects, doctrine) a question.", {"question": {"type": "string"}, "k": {"type": "integer"}}, ["question"],
     lambda a: ["brain", "ask", a["question"], "-k", str(a.get("k", 8))]),
    ("vm_brain_log", "After a film: log it in the ledger and the vault, with the user's verdict.", {"film": F, "verdict": {"type": "string"}, "good": {"type": "boolean"}, "bad": {"type": "boolean"}}, ["film"],
     lambda a: ["brain", "log", a["film"]] + (["--verdict", a["verdict"]] if a.get("verdict") else []) + (["--good"] if a.get("good") else []) + (["--bad"] if a.get("bad") else [])),
    ("vm_brain_sync", "Rebuild the director's vault and its index from the skill and the ledger.", {}, [], lambda a: ["brain", "sync"]),
    ("vm_openfilm", "The editable timeline in OpenFilm Studio: setup (image-bridge provider + skill), export <film> (every effect, chapter, voice, music entrance and hook sound its own clip), open <film> (prints Studio's address), render <film> (the hand-edited timeline at -14 LUFS), diff <film> (what the person changed).",
     {"action": {"type": "string", "enum": ["setup", "export", "open", "render", "diff", "studio"]}, "film": F}, ["action"],
     lambda a: ["openfilm", a["action"]] + ([a["film"]] if a.get("film") else [])),
    ("vm_studio", "EDITOR FIRST: open the film in OpsGen (the person watches); every later vm stage updates the timeline live.", {"film": F}, ["film"], lambda a: ["studio", a["film"]]),
    ("vm_tl", "The OpsGen timeline in a few lines (every clip id and time): cheap to read before editing.", {"film": F}, ["film"], lambda a: ["tl", a["film"]]),
    ("vm_edit", "Edit the OpsGen timeline with JSON operations (add move trim len set delete dup split ramp freeze kf fade ripple track), atomically.", {"film": F, "ops": {"type": "string", "description": "JSON op or list of ops"}}, ["film", "ops"], lambda a: ["edit", a["film"], a["ops"]]),
    ("vm_media", "Footage edits that need new pixels or sound: reverse, stabilize, denoise, key (chroma -> alpha webm), reframe (auto 16:9 -> 9:16 following the subject), track (CSRT motion tracking -> keyframes to pin an overlay), beats (cut points of a song), broll (a picture/clip on a spoken word). args: the op's command-line arguments, e.g. [\"reframe\", \"in.mp4\", \"-o\", \"out.mp4\"].",
     {"args": {"type": "array", "items": {"type": "string"}}}, ["args"], lambda a: ["media", *a["args"]]),
    ("vm_doctor", "What this machine has (tools, image bridge, 3D, disk).", {}, [], lambda a: ["doctor"]),
]
BY = {t[0]: t for t in TOOLS}


def call(name: str, args: dict) -> tuple[str, bool]:
    t = BY.get(name)
    if not t:
        return f"unknown tool {name}", True
    missing = [k for k in t[3] if k not in args]
    if missing:
        return f"missing arguments: {missing}", True
    cmd = [sys.executable, str(S / "vm.py"), "--json", *map(str, t[4](args))]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=7200)
    text = r.stdout.strip() or r.stderr.strip()
    if r.returncode != 0:
        return (text + "\n" + r.stderr.strip())[-6000:], True
    return text[-60000:], False


def reply(mid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": mid}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def serve():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            reply(None, error={"code": -32700, "message": "parse error"})
            continue
        method, mid = m.get("method"), m.get("id")
        if mid is None:          # a notification
            continue
        if method == "initialize":
            reply(mid, {"protocolVersion": m.get("params", {}).get("protocolVersion", PROTOCOL),
                        "capabilities": {"tools": {"listChanged": False}},
                        "serverInfo": {"name": "claude-editor-vm", "version": "1.0.0"},
                        "instructions": "Claude Editor (Video Mania). Start with vm_status or vm_new. Rules: references/editor-effects-and-hook-sound.md, house-rules.md. "
                                        "Asset-first: generate pictures before drawing in code. Every film gets vm_fx (hook on frame 0)."})
        elif method == "ping":
            reply(mid, {})
        elif method == "tools/list":
            reply(mid, {"tools": [{"name": n, "description": d, "inputSchema": {"type": "object", "properties": props, "required": req}}
                                  for n, d, props, req, _ in TOOLS]})
        elif method == "tools/call":
            p = m.get("params", {})
            try:
                text, err = call(p.get("name"), p.get("arguments") or {})
            except Exception as ex:
                text, err = f"{type(ex).__name__}: {ex}", True
            reply(mid, {"content": [{"type": "text", "text": text}], "isError": err})
        else:
            reply(mid, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    serve()

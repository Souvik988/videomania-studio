"""Video Mania engines: the exact upstream repos the skill directs.

    python vm_engines.py list              one line per engine: lane, licence, present or missing
    python vm_engines.py doctor            what each engine needs on this machine and what is missing
    python vm_engines.py sync [id ...]     clone missing engines; --update also moves present ones to upstream HEAD
    python vm_engines.py path <id>         print an engine's folder (for other scripts)
    python vm_engines.py pin               write the commits currently checked out back into engines.json

Engines live under <workbench>/research (outside any synced folder). engines/engines.json is the
registry: repo, pinned commit, lanes, licence, what to read first, what it needs.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import vm_env

REGISTRY = vm_env.SKILL_DIR / "engines" / "engines.json"


def registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def root() -> Path:
    return vm_env.workbench() / registry().get("root", "research")


def engine_dir(e: dict) -> Path:
    return (root() / e["dir"]).resolve()


def find(eid: str) -> dict:
    for e in registry()["engines"]:
        if e["id"] == eid:
            return e
    raise SystemExit(f"unknown engine '{eid}'. Run: python vm_engines.py list")


def git(args: list[str], cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=check)


def head(d: Path) -> str:
    r = git(["rev-parse", "--short=12", "HEAD"], cwd=d)
    return r.stdout.strip() if r.returncode == 0 else ""


def cmd_list(_: argparse.Namespace) -> int:
    for e in registry()["engines"]:
        d = engine_dir(e)
        state = "ok" if d.exists() else "MISSING"
        if state == "ok" and (d / ".git").exists():
            h = head(d)
            if h and not h.startswith(e["commit"][:12]) and not e["commit"].startswith(h):
                state = f"ok (at {h}, pinned {e['commit']})"
        print(f"{e['id']:<26} {','.join(e['lanes']):<28} {state:<12} {e['licence']}")
    return 0


TOOLS = {
    "node": ["node", "--version"],
    "python": [sys.executable, "--version"],
    "ffmpeg": ["ffmpeg", "-version"],
    "git": ["git", "--version"],
    "uv": ["uv", "--version"],
    "raea": ["raea", "--version"],
    "aseprite": ["aseprite", "--version"],
    "pnpm": ["pnpm", "--version"],
}


def tool_version(name: str) -> str | None:
    exe = shutil.which(TOOLS[name][0])
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *TOOLS[name][1:]], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    out = (r.stdout or r.stderr).strip().splitlines()
    return out[0][:60] if out else "present"


def cmd_doctor(_: argparse.Namespace) -> int:
    print("Tools on this machine")
    for name in TOOLS:
        v = tool_version(name)
        print(f"  {name:<9} {v if v else 'not found'}")
    print("\nEngines")
    missing = 0
    for e in registry()["engines"]:
        d = engine_dir(e)
        ok = d.exists()
        missing += 0 if ok else 1
        print(f"  [{'x' if ok else ' '}] {e['id']:<26} {d if ok else 'not cloned: python vm_engines.py sync ' + e['id']}")
        for n in e.get("needs", []):
            print(f"        needs: {n}")
        if e.get("notes"):
            print(f"        note:  {e['notes']}")
    print(f"\n{len(registry()['engines']) - missing} of {len(registry()['engines'])} engines present.")
    return 0 if missing == 0 else 1


def cmd_sync(a: argparse.Namespace) -> int:
    root().mkdir(parents=True, exist_ok=True)
    engines = [find(i) for i in a.ids] if a.ids else registry()["engines"]
    failed = 0
    for e in engines:
        d = engine_dir(e)
        if d.exists():
            if a.update and (d / ".git").exists():
                r = git(["pull", "--ff-only", "-q"], cwd=d)
                print(f"{e['id']}: {'updated to ' + head(d) if r.returncode == 0 else 'pull failed: ' + r.stderr.strip()[:120]}")
                failed += 0 if r.returncode == 0 else 1
            else:
                print(f"{e['id']}: present")
            continue
        r = git(["clone", "-q", e["repo"], str(d)])
        if r.returncode != 0:
            print(f"{e['id']}: clone failed: {r.stderr.strip()[:160]}")
            failed += 1
            continue
        git(["checkout", "-q", e["commit"]], cwd=d)
        print(f"{e['id']}: cloned at {head(d)}")
    return 1 if failed else 0


def cmd_path(a: argparse.Namespace) -> int:
    print(engine_dir(find(a.id)))
    return 0


def cmd_pin(_: argparse.Namespace) -> int:
    reg = registry()
    changed = 0
    for e in reg["engines"]:
        d = engine_dir(e)
        h = head(d) if d.exists() else ""
        if h and h != e["commit"]:
            e["commit"] = h
            changed += 1
    REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"pinned {changed} engine(s) to their checked-out commits")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    sub.add_parser("doctor").set_defaults(fn=cmd_doctor)
    s = sub.add_parser("sync")
    s.add_argument("ids", nargs="*")
    s.add_argument("--update", action="store_true")
    s.set_defaults(fn=cmd_sync)
    s = sub.add_parser("path")
    s.add_argument("id")
    s.set_defaults(fn=cmd_path)
    sub.add_parser("pin").set_defaults(fn=cmd_pin)
    a = p.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())

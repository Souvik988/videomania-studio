"""Shared helpers for Video Mania skill scripts.

Locates the production workbench (OpenMontage checkout + venv), runs
subprocesses with explicit argument lists (never shell strings), and wraps
ffprobe. Every script imports this first.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
HF_VERSION = os.environ.get("VIDEOMANIA_HF_VERSION", "0.8.166")


def workbench() -> Path:
    env = os.environ.get("VIDEOMANIA_WORKBENCH")
    candidates = [Path(env)] if env else []
    candidates += [Path.home() / "video-production-workbench"]
    cfg = SKILL_DIR / "config.json"
    if cfg.exists():
        try:
            candidates.insert(0, Path(json.loads(cfg.read_text(encoding="utf-8"))["workbench"]))
        except (KeyError, json.JSONDecodeError):
            pass
    for c in candidates:
        if (c / "OpenMontage" / "AGENT_GUIDE.md").exists():
            return c
    raise SystemExit(
        "Video Mania workbench not found. Set VIDEOMANIA_WORKBENCH or run "
        f"{SKILL_DIR / 'scripts' / 'bootstrap.sh'} to create ~/video-production-workbench."
    )


def openmontage() -> Path:
    return workbench() / "OpenMontage"


def venv_python() -> Path:
    om = openmontage()
    for p in (om / ".venv" / "Scripts" / "python.exe", om / ".venv" / "bin" / "python"):
        if p.exists():
            return p
    raise SystemExit(f"OpenMontage venv missing under {om / '.venv'}; run bootstrap.")


def ensure_openmontage_on_path() -> Path:
    """Make `import tools...`, `import lib...` resolve to the OpenMontage checkout.

    Scripts must run under the OpenMontage venv; re-exec there if not.
    """
    om = openmontage()
    # config.json may point projects somewhere else (cloud: the repo's projects/ so results can be pushed)
    cfg = SKILL_DIR / "config.json"
    if cfg.exists() and not os.environ.get("OPENMONTAGE_PROJECTS_DIR"):
        try:
            pd = json.loads(cfg.read_text(encoding="utf-8")).get("projects_dir")
            if pd:
                os.environ["OPENMONTAGE_PROJECTS_DIR"] = pd
        except json.JSONDecodeError:
            pass
    vp = venv_python()
    if Path(sys.executable).resolve() != vp.resolve() and not os.environ.get("VIDEOMANIA_NO_REEXEC"):
        env = dict(os.environ, VIDEOMANIA_NO_REEXEC="1")
        r = subprocess.run([str(vp), *sys.argv], env=env)
        raise SystemExit(r.returncode)
    if str(om) not in sys.path:
        sys.path.insert(0, str(om))
    os.chdir(om)  # OpenMontage tools resolve relative paths/config from repo root
    return om


def run(cmd: list[str], *, check: bool = True, timeout: float | None = None, cwd: str | Path | None = None) -> subprocess.CompletedProcess:
    exe = shutil.which(cmd[0]) or cmd[0]
    proc = subprocess.run([exe, *cmd[1:]], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, cwd=cwd)
    if check and proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-1500:]
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(map(str, cmd[:6]))} ...\n{tail}")
    return proc


def npx_hf(args: list[str], **kw) -> subprocess.CompletedProcess:
    return run(["npx", "--yes", f"hyperframes@{HF_VERSION}", *args], **kw)


def ffprobe(path: str | Path) -> dict:
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(p.stdout)


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


PROJECT_SUBDIRS = [
    "input", "brief", "transcript", "storyboard", "assets", "source", "audio/stems",
    "previews", "qa", "delivery/audio-stems", "delivery/editable-project",
]


def project_dir(project_id: str) -> Path:
    from lib.paths import PROJECTS_DIR  # OpenMontage's single source of truth
    return Path(PROJECTS_DIR) / project_id


def write_json(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def loudness(path: str | Path) -> dict:
    """Integrated loudness, LRA and true peak via ffmpeg ebur128."""
    p = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], check=True)
    out = p.stderr
    res: dict = {}
    summary = out[out.rfind("Summary:"):]
    for line in summary.splitlines():
        line = line.strip()
        if line.startswith("I:"):
            res["integrated_lufs"] = float(line.split()[1])
        elif line.startswith("LRA:"):
            res["lra_lu"] = float(line.split()[1])
        elif line.startswith("Peak:"):
            res["true_peak_dbtp"] = float(line.split()[1])
    return res

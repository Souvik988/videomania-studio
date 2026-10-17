"""Video Mania preflight: what can this machine actually do right now?

Usage: preflight.py [--input PATH ...] [--json]

Reports runtimes (ffmpeg, node, HyperFrames, Remotion), OpenMontage registry
capability counts, local ASR/music/SFX availability, RAM/disk, and input
file sanity. Prints JSON; exit 0 = passed/degraded, 2 = blocked.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vm_env  # noqa: E402


def mem_info() -> dict:
    try:
        import ctypes

        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong), ("c", ctypes.c_ulonglong),
                        ("d", ctypes.c_ulonglong), ("e", ctypes.c_ulonglong)]
        m = MS()
        m.dwLength = ctypes.sizeof(MS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
        return {"total_gb": round(m.ullTotalPhys / 2**30, 1), "available_gb": round(m.ullAvailPhys / 2**30, 1)}
    except Exception:  # non-Windows
        try:
            info = Path("/proc/meminfo").read_text().split("\n")
            kv = {l.split(":")[0]: int(l.split()[1]) for l in info if ":" in l}
            return {"total_gb": round(kv["MemTotal"] / 2**20, 1), "available_gb": round(kv["MemAvailable"] / 2**20, 1)}
        except Exception:
            return {}


def probe_http(url: str, timeout: float = 1.5, bearer: str | None = None) -> dict:
    """Loopback liveness only — never leaves this machine, and only replays a token
    this process already has in its own environment.

    401 counts as reachable: a running engine refuses unauthenticated routes, and
    'up but refused' is a different remedy from 'not running'.
    """
    import urllib.error
    import urllib.request
    headers = {"Authorization": f"Bearer {bearer}"} if bearer else {}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"reachable": True, "status": resp.status, "ok": 200 <= resp.status < 400}
    except urllib.error.HTTPError as exc:
        return {"reachable": True, "status": exc.code, "ok": False, "needs_token": exc.code == 401}
    except Exception as exc:  # noqa: BLE001
        return {"reachable": False, "ok": False, "error": type(exc).__name__}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", action="append", default=[])
    args = ap.parse_args()
    om = vm_env.ensure_openmontage_on_path()
    report: dict = {"workbench": str(vm_env.workbench()), "openmontage": str(om), "blockers": [], "warnings": []}

    for b in ("ffmpeg", "ffprobe", "node", "npx"):
        report[b] = bool(shutil.which(b))
        if not report[b]:
            report["blockers"].append(f"{b} not on PATH")

    try:
        head = vm_env.run(["git", "-C", str(om), "rev-parse", "--short", "HEAD"], check=False).stdout.strip()
        report["openmontage_commit"] = head
    except Exception:
        pass

    from tools.tool_registry import registry
    registry.discover()
    summary = registry.provider_menu_summary()
    report["composition_runtimes"] = summary["composition_runtimes"]
    report["capabilities"] = {c["capability"]: f"{c['configured']}/{c['total']}" for c in summary["capabilities"]}
    report["runtime_warnings"] = summary.get("runtime_warnings", [])
    if not summary["composition_runtimes"].get("hyperframes"):
        report["warnings"].append("HyperFrames runtime not available — run `npx --yes hyperframes doctor`")

    local = {}
    for tool in ("transcriber", "procedural_score", "procedural_sfx", "audio_mixer", "subtitle_gen", "audio_enhance"):
        t = registry._tools.get(tool)
        local[tool] = t.get_info()["status"] if t else "missing"
    report["local_tools"] = local
    if local.get("transcriber") != "available":
        report["warnings"].append("transcriber unavailable: pip install faster-whisper into the OpenMontage venv")

    disk = shutil.disk_usage(str(om))
    report["disk_free_gb"] = round(disk.free / 2**30, 1)
    report["memory"] = mem_info()
    if report["memory"].get("available_gb", 99) < 1.5:
        report["warnings"].append(
            f"Low free RAM ({report['memory'].get('available_gb')} GB): render with --workers 1 and draft previews first")
    if report["disk_free_gb"] < 5:
        report["blockers"].append("less than 5 GB free disk")

    report["inputs"] = []
    for p in args.input:
        path = Path(p)
        entry = {"path": str(path), "exists": path.exists()}
        if path.exists():
            try:
                pr = vm_env.ffprobe(path)
                entry["duration_s"] = float(pr["format"].get("duration", 0))
                entry["streams"] = [s["codec_type"] + ":" + s.get("codec_name", "?") for s in pr["streams"]]
            except Exception as e:  # noqa: BLE001
                entry["error"] = f"unreadable media: {e}"[:300]
                report["blockers"].append(f"input unreadable: {path}")
        else:
            report["blockers"].append(f"input missing: {path}")
        report["inputs"].append(entry)

    report["google_flow_mcp"] = (
        "Not detectable from a script. The agent must check its own tool list for a Google Flow MCP "
        "server (and `claude mcp list`). If absent: BLOCKED/not configured — use local fallbacks."
    )
    # What a script *can* see: whether the Flow engine and its local endpoints answer.
    engine = Path(os.environ.get(
        "FLOW_MCP_DIR", str(Path.home() / "video-production-workbench" / "mcp" / "google-flow-mcp")))
    api = probe_http(os.environ.get("FLOW_ASSET_API_URL", "http://127.0.0.1:4318").rstrip("/") + "/v1/health",
                     bearer=os.environ.get("FLOW_HTTP_TOKEN") or None)
    cdp = probe_http(os.environ.get("FLOW_BROWSER_CDP_URL", "http://127.0.0.1:9222") + "/json/version")
    installed = (engine / "dist" / "asset-mcp-main.js").is_file()
    if not installed:
        state = "absent"
    elif api.get("ok"):
        state = "live"
    elif api.get("needs_token"):
        state = "token_missing" if not os.environ.get("FLOW_HTTP_TOKEN") else "token_mismatch"
    elif cdp.get("ok"):
        state = "browser_only"
    else:
        state = "engine_down"
    report["google_flow_engine"] = {
        "dir": str(engine), "installed": installed, "asset_api": api, "browser_cdp": cdp, "state": state,
        "note": "'browser_only' means the signed-in Flow Chrome is up but no loopback job API: agents can "
                "still generate over MCP; pipeline tools (google_flow_video/image) cannot.",
    }
    if state == "absent":
        report["warnings"].append(
            "No Google Flow engine at the expected path — generated-media beats fall back to coded graphics. "
            "Clone google-flow-mcp, npm install && npm run build, or set FLOW_MCP_DIR.")
    elif state in ("token_missing", "token_mismatch"):
        report["warnings"].append(
            f"Flow job API is up but this process cannot authenticate ({state}). Set FLOW_HTTP_TOKEN in "
            "OpenMontage/.env to the value in the engine's .env.asset-studio.")
    elif state in ("engine_down", "browser_only"):
        report["warnings"].append(
            "Flow engine not serving its job API — pipeline tools report it as degraded. "
            "`npm run host` in the engine checkout, or generate through the mcp__google-flow__* tools.")
    report["status"] = "blocked" if report["blockers"] else ("degraded" if report["warnings"] else "passed")
    print(json.dumps(report, indent=2))
    return 2 if report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

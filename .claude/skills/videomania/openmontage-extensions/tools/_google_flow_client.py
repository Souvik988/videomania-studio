"""Loopback client for the user's own Google Flow engine (google-flow-mcp).

The engine is one server with two front doors: IDE agents drive it over MCP (stdio),
and pipeline tools like `google_flow_video` reach the same durable job system through
its local HTTP API (`npm run host`). Both paths submit the same job, so a clip produced
by the registry and a clip produced by an agent are the same asset with the same ledger.

Only 127.0.0.1 is ever contacted, and the bearer token comes from the environment. No
Google credential, cookie or OTP passes through this module — sign-in is a human action
in the engine's own Chrome window.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_ENGINE = Path.home() / "video-production-workbench" / "mcp" / "google-flow-mcp"
ENTRYPOINT = Path("dist") / "asset-mcp-main.js"

STATUS_CACHE_TTL_S = 30.0
_STATUS_CACHE: dict[str, Any] = {"checked_at": 0.0, "available": False, "detail": "never probed"}

TERMINAL_FAILURES = {
    "AUTH_REQUIRED", "UI_CHANGED", "DOWNLOAD_FAILED", "GENERATION_FAILED",
    "TIMEOUT", "QUALITY_REJECTED", "INVALID_OUTPUT", "RECOVERY_REQUIRED", "CANCELLED",
}


class FlowEngineError(RuntimeError):
    """The engine is unreachable or refused/reported the job. Message names the remedy."""


def engine_dir() -> Path:
    return Path(os.environ.get("FLOW_MCP_DIR", str(DEFAULT_ENGINE))).expanduser()


def installed() -> bool:
    return (engine_dir() / ENTRYPOINT).is_file()


def api_base() -> str:
    return os.environ.get("FLOW_ASSET_API_URL", "http://127.0.0.1:4318").rstrip("/")


def token() -> str:
    return os.environ.get("FLOW_HTTP_TOKEN", "")


def _request(method: str, path: str, payload: dict | None = None, timeout: float = 10.0) -> tuple[int, dict]:
    if not token():
        raise FlowEngineError(
            "FLOW_HTTP_TOKEN is not set. The Flow asset API refuses unauthenticated job submissions; "
            "put the same token in .env for the engine and in this environment."
        )
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        api_base() + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token()}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise FlowEngineError(f"Flow API {method} {path} -> HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise FlowEngineError(
            f"Flow engine not answering on {api_base()} ({exc}). Start it with `npm run host` in "
            f"{engine_dir()}, or drive the same engine through the mcp__google-flow__* tools."
        ) from exc


def session_state(*, refresh: bool = False) -> dict:
    """Cached liveness probe so registry discovery never blocks on a dead socket."""
    now = time.time()
    if not refresh and now - _STATUS_CACHE["checked_at"] < STATUS_CACHE_TTL_S:
        return dict(_STATUS_CACHE)
    available, detail = False, ""
    if not installed():
        detail = f"no Flow engine at {engine_dir()} (clone google-flow-mcp and run npm install && npm run build)"
    else:
        try:
            status, body = _request("GET", "/v1/health", timeout=1.5)
            available = 200 <= status < 400
            detail = f"{api_base()} healthy: " + json.dumps(body)[:200]
        except FlowEngineError as exc:
            detail = str(exc)
    _STATUS_CACHE.update(checked_at=now, available=available, detail=detail)
    return dict(_STATUS_CACHE)


def submit(kind: str, prompt: str, *, duration: str = "8s", model: str = "gemini-omni-flash",
           aspect_ratio: str = "16:9", output_count: int | None = None,
           reference_image_paths: list[str] | None = None, idempotency_key: str | None = None) -> dict:
    payload: dict[str, Any] = {
        "kind": kind, "prompt": prompt, "model": model,
        "aspectRatio": aspect_ratio, "priority": "NORMAL",
    }
    if kind == "image":
        payload["outputCount"] = output_count or 1
    else:
        payload["duration"] = duration
    if reference_image_paths:
        payload["referenceImagePaths"] = list(reference_image_paths)
    if idempotency_key:
        payload["idempotencyKey"] = idempotency_key
    _, job = _request("POST", "/v1/jobs", payload, timeout=30.0)
    return job


def poll(job_id: str) -> dict:
    _, job = _request("GET", f"/v1/jobs/{job_id}", timeout=15.0)
    return job


def wait(job: dict, *, max_wait_s: float = 900.0, interval_s: float = 5.0) -> dict:
    deadline = time.time() + max_wait_s
    while job.get("status") not in {"COMPLETED", *TERMINAL_FAILURES}:
        if time.time() > deadline:
            raise FlowEngineError(
                f"Job {job.get('jobId')} still {job.get('status')} after {max_wait_s:.0f}s. "
                "Do not resubmit — poll again, or call recover_video_job once it is terminal."
            )
        time.sleep(interval_s)
        job = poll(job["jobId"])
    return job


def delivery_path(job: dict) -> Path:
    delivery = job.get("delivery") or {}
    local = delivery.get("localPath") or (job.get("output") or {}).get("finalPath")
    if not local:
        err = job.get("error") or {}
        raise FlowEngineError(
            f"Job {job.get('jobId')} has status {job.get('status')} but no delivered file. "
            f"Engine error: {json.dumps(err)[:300]}"
        )
    return Path(local)

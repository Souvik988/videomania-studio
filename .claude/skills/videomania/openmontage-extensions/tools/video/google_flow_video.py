"""Google Flow video generation, through the user's own signed-in Google account.

The engine is the local `google-flow-mcp` server: it drives a persistent Chrome profile
at flow.google.com and returns durable jobs. Nothing here talks to Google directly, and
nothing here can spend credits without the caller passing an `approval` string that
quotes what the user actually agreed to — the standing rule for this provider is one
explicit approval per generation, so the tool refuses to guess.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from tools import _google_flow_client as flow
from tools.base_tool import (
    BaseTool,
    Determinism,
    ExecutionMode,
    ResourceProfile,
    RetryPolicy,
    ResumeSupport,
    ToolResult,
    ToolRuntime,
    ToolStability,
    ToolStatus,
    ToolTier,
)
from tools.video._shared import probe_output

FLOW_LICENSE = (
    "Generated through the user's own Google Flow account under Google's Terms of Service; "
    "no third-party stock licence applies. Watermark handling is recorded per job."
)


class GoogleFlowVideo(BaseTool):
    name = "google_flow_video"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "video_generation"
    provider = "google_flow"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.HYBRID

    dependencies: list[str] = []
    install_instructions = (
        "Install the Google Flow engine once per machine:\n"
        "  1. git clone https://github.com/Souvik988/google-flow-mcp && cd google-flow-mcp\n"
        "  2. npm install && npm run build\n"
        "  3. set FLOW_HTTP_TOKEN (>=24 chars) and FLOW_MCP_DIR (defaults to "
        "~/video-production-workbench/mcp/google-flow-mcp)\n"
        "  4. npm run host   # loopback job API on 127.0.0.1:4318\n"
        "  5. sign in once in the visible Chrome window (flow_browser_login). Google passwords, "
        "cookies and OTP codes are never handled by this toolchain."
    )
    agent_skills = ["gemini-omni", "ai-video-gen"]

    capabilities = ["text_to_video", "image_to_video", "reference_to_video"]
    supports = {
        "reference_image": True,
        "native_audio": False,
        "offline": False,
        "local_gpu": False,
        "human_auth_session": True,
        "durable_jobs": True,
    }
    best_for = [
        "cinematic or photographic plates for a voiceover beat that code cannot draw",
        "the user's own Google Flow credits instead of a paid API key",
        "shot-consistent clips that arrive already finished and locally delivered",
    ]
    not_good_for = [
        "text, UI, charts, logos or anything that must be exact — always code those",
        "unattended batch runs: each generation needs its own explicit user approval",
        "machines with no signed-in Flow browser session",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt", "approval"],
        "properties": {
            "prompt": {"type": "string", "description": "Art-directed shot instruction"},
            "approval": {"type": "string", "description": "Quote of the user's approval for THIS generation"},
            "duration": {"type": "string", "enum": ["4s", "6s", "8s", "10s"], "default": "8s"},
            "model": {"type": "string", "enum": ["gemini-omni-flash", "veo-3.1-fast", "veo-3.1-quality"],
                      "default": "gemini-omni-flash"},
            "aspect_ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "3:4", "4:3"], "default": "16:9"},
            "reference_image_paths": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "idempotency_key": {"type": "string"},
            "output_path": {"type": "string", "description": "Project-relative path to copy the delivered clip into"},
            "wait_for_completion": {"type": "boolean", "default": True},
            "max_wait_seconds": {"type": "number", "default": 900},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=1500, vram_mb=0, disk_mb=3000, network_required=True)
    # max_retries=0 is deliberate: a retried submission is a second paid render.
    retry_policy = RetryPolicy(max_retries=0)
    resume_support = ResumeSupport.FROM_CHECKPOINT
    idempotency_key_fields = ["prompt", "duration", "model", "aspect_ratio"]
    side_effects = [
        "spends the user's Google Flow credits",
        "opens a job folder under outputs/<job-id>/ in the engine workspace",
        "drives a visible Chrome window on the user's automation profile",
    ]
    user_visible_verification = [
        "Watch the delivered clip before it enters the edit: geometry, hands, motion drift, invented text"
    ]

    def get_status(self) -> ToolStatus:
        if not flow.installed():
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE if flow.session_state()["available"] else ToolStatus.DEGRADED

    def estimate_cost(self, inputs: dict[str, object]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, object]) -> float:
        return 240.0

    def get_info(self) -> dict[str, object]:
        info = super().get_info()
        info["engine_dir"] = str(flow.engine_dir())
        info["flow_session"] = flow.session_state()["detail"][:300]
        info["setup_offer"] = {
            "kind": "local_server",
            "env_var": "FLOW_MCP_DIR",
            "default_url": flow.api_base(),
            "health_check": "/v1/health",
            "what_it_unlocks": "Google Flow video generation on the user's own account (Omni Flash, 4-10s)",
        }
        return info

    def execute(self, inputs: dict[str, object]) -> ToolResult:
        approval = str(inputs.get("approval") or "").strip()
        if not approval:
            return ToolResult(
                success=False,
                error="google_flow_video needs an `approval` string quoting the user's approval for this "
                      "specific generation. Generation spends their credits, so it is never automatic.",
            )
        if not flow.installed():
            return ToolResult(success=False, error=f"No Google Flow engine at {flow.engine_dir()}. " + self.install_instructions)
        state = flow.session_state(refresh=True)
        if not state["available"]:
            return ToolResult(success=False, error=f"Flow engine installed but its job API is not answering. {state['detail']}")

        prompt = str(inputs.get("prompt") or "").strip()
        refs = [str(p) for p in (inputs.get("reference_image_paths") or [])]
        start = time.time()
        try:
            job = flow.submit(
                "video", prompt,
                duration=str(inputs.get("duration") or "8s"),
                model=str(inputs.get("model") or "gemini-omni-flash"),
                aspect_ratio=str(inputs.get("aspect_ratio") or "16:9"),
                reference_image_paths=refs or None,
                idempotency_key=inputs.get("idempotency_key"),
            )
            if inputs.get("wait_for_completion") is False:
                return ToolResult(
                    success=True,
                    data={"job_id": job["jobId"], "status": job["status"], "provider": self.provider,
                          "prompt": prompt, "approval": approval, "submitted_only": True},
                )
            job = flow.wait(job, max_wait_s=float(inputs.get("max_wait_seconds") or 900))
            source = flow.delivery_path(job)
        except flow.FlowEngineError as exc:
            return ToolResult(success=False, error=str(exc))

        delivered = source
        if inputs.get("output_path"):
            target = Path(str(inputs["output_path"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            delivered = target

        watermark = (job.get("output") or {}).get("watermark") or {}
        return ToolResult(
            success=True,
            data={
                "output": str(delivered),
                "engine_output": str(source),
                "provider": self.provider,
                "model": str(inputs.get("model") or "gemini-omni-flash"),
                "prompt": prompt,
                "approval": approval,
                "job_id": job.get("jobId"),
                "status": job.get("status"),
                "duration_setting": inputs.get("duration") or "8s",
                "aspect_ratio": inputs.get("aspect_ratio") or "16:9",
                "format": "mp4",
                "watermark_removed": watermark.get("removed") is True,
                "compiled_prompt": job.get("compiledPrompt"),
                "license": FLOW_LICENSE,
                "workflow_provenance": {
                    "source": "google-flow-mcp", "engine_dir": str(flow.engine_dir()),
                    "approval": approval, "job_events": len(job.get("events") or []),
                },
                "provenance": {
                    "source": "user_google_flow_account", "generator": "google_flow_video",
                    "third_party_audio": False, "license": FLOW_LICENSE,
                },
                **probe_output(delivered),
            },
            artifacts=[str(delivered)],
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            model=str(inputs.get("model") or "gemini-omni-flash"),
        )

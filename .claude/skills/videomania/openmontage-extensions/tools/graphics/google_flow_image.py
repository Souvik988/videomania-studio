"""Google Flow still-image generation, through the user's own signed-in account.

Same engine and same credit-approval rule as `google_flow_video`: this draws plates,
textures and metaphor stills that code cannot produce, and refuses to run without an
`approval` string quoting what the user agreed to.
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

IMAGE_LICENSE = (
    "Generated through the user's own Google Flow account under Google's Terms of Service; "
    "no third-party stock licence applies."
)


class GoogleFlowImage(BaseTool):
    name = "google_flow_image"
    version = "1.0.0"
    tier = ToolTier.GENERATE
    capability = "image_generation"
    provider = "google_flow"
    stability = ToolStability.BETA
    execution_mode = ExecutionMode.SYNC
    determinism = Determinism.STOCHASTIC
    runtime = ToolRuntime.HYBRID

    dependencies: list[str] = []
    install_instructions = (
        "Needs the same Google Flow engine as google_flow_video: clone google-flow-mcp, "
        "`npm install && npm run build`, set FLOW_HTTP_TOKEN, then `npm run host` and sign in "
        "once in its Chrome window. See google_flow_video for the full steps."
    )
    agent_skills = ["gemini-omni"]

    capabilities = ["text_to_image", "image_edit", "reference_to_image"]
    supports = {
        "reference_image": True,
        "offline": False,
        "local_gpu": False,
        "human_auth_session": True,
        "variations": True,
    }
    best_for = [
        "still plates, backdrops and visual metaphors behind coded typography",
        "x1-x4 variations of one idea in a single job",
        "the user's own Flow credits instead of a separate image API key",
    ]
    not_good_for = [
        "readable text, UI chrome, charts, logos or anything that must be pixel-exact",
        "unattended batch runs — each generation needs its own approval",
    ]

    input_schema = {
        "type": "object",
        "required": ["prompt", "approval"],
        "properties": {
            "prompt": {"type": "string"},
            "approval": {"type": "string", "description": "Quote of the user's approval for THIS generation"},
            "aspect_ratio": {"type": "string", "enum": ["16:9", "9:16", "1:1", "3:4", "4:3"], "default": "16:9"},
            "output_count": {"type": "integer", "minimum": 1, "maximum": 4, "default": 1},
            "style": {"type": "string"},
            "reference_image_paths": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "idempotency_key": {"type": "string"},
            "output_path": {"type": "string"},
            "wait_for_completion": {"type": "boolean", "default": True},
            "max_wait_seconds": {"type": "number", "default": 600},
        },
    }

    resource_profile = ResourceProfile(cpu_cores=2, ram_mb=1200, vram_mb=0, disk_mb=800, network_required=True)
    retry_policy = RetryPolicy(max_retries=0)
    resume_support = ResumeSupport.FROM_CHECKPOINT
    idempotency_key_fields = ["prompt", "aspect_ratio", "output_count"]
    side_effects = [
        "spends the user's Google Flow credits",
        "opens a job folder under outputs/<job-id>/ in the engine workspace",
        "drives a visible Chrome window on the user's automation profile",
    ]
    user_visible_verification = ["Inspect the still at export size for warped geometry or invented text before use"]

    def get_status(self) -> ToolStatus:
        if not flow.installed():
            return ToolStatus.UNAVAILABLE
        return ToolStatus.AVAILABLE if flow.session_state()["available"] else ToolStatus.DEGRADED

    def estimate_cost(self, inputs: dict[str, object]) -> float:
        return 0.0

    def estimate_runtime(self, inputs: dict[str, object]) -> float:
        return 120.0

    def get_info(self) -> dict[str, object]:
        info = super().get_info()
        info["engine_dir"] = str(flow.engine_dir())
        info["flow_session"] = flow.session_state()["detail"][:300]
        return info

    def execute(self, inputs: dict[str, object]) -> ToolResult:
        approval = str(inputs.get("approval") or "").strip()
        if not approval:
            return ToolResult(
                success=False,
                error="google_flow_image needs an `approval` string quoting the user's approval for this "
                      "specific generation. It spends their credits, so it is never automatic.",
            )
        if not flow.installed():
            return ToolResult(success=False, error=f"No Google Flow engine at {flow.engine_dir()}. " + self.install_instructions)
        state = flow.session_state(refresh=True)
        if not state["available"]:
            return ToolResult(success=False, error=f"Flow engine installed but its job API is not answering. {state['detail']}")

        prompt = str(inputs.get("prompt") or "").strip()
        if inputs.get("style"):
            # The job API has no style field; Flow reads style from the instruction itself.
            prompt = f"{prompt}. Visual style: {inputs['style']}"
        refs = [str(p) for p in (inputs.get("reference_image_paths") or [])]
        start = time.time()
        try:
            job = flow.submit(
                "image", prompt,
                aspect_ratio=str(inputs.get("aspect_ratio") or "16:9"),
                output_count=int(inputs.get("output_count") or 1),
                reference_image_paths=refs or None,
                idempotency_key=inputs.get("idempotency_key"),
            )
            if inputs.get("wait_for_completion") is False:
                return ToolResult(success=True, data={"job_id": job["jobId"], "status": job["status"],
                                                      "provider": self.provider, "prompt": prompt,
                                                      "approval": approval, "submitted_only": True})
            job = flow.wait(job, max_wait_s=float(inputs.get("max_wait_seconds") or 600))
            source = flow.delivery_path(job)
        except flow.FlowEngineError as exc:
            return ToolResult(success=False, error=str(exc))

        siblings = sorted(p for p in source.parent.glob("*") if p.is_file()) if source.parent.is_dir() else [source]
        delivered = source
        copies: list[Path] = []
        if inputs.get("output_path"):
            target = Path(str(inputs["output_path"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            delivered = target
            for extra in siblings:
                if extra != source:
                    dest = target.parent / f"{target.stem}_{extra.stem}{extra.suffix}"
                    shutil.copy2(extra, dest)
                    copies.append(dest)

        return ToolResult(
            success=True,
            data={
                "output": str(delivered),
                "engine_output": str(source),
                "additional_outputs": [str(p) for p in copies],
                "provider": self.provider,
                "model": "google-flow-image",
                "prompt": prompt,
                "approval": approval,
                "job_id": job.get("jobId"),
                "status": job.get("status"),
                "aspect_ratio": inputs.get("aspect_ratio") or "16:9",
                "format": delivered.suffix.lstrip(".") or "png",
                "variations": len(siblings),
                "license": IMAGE_LICENSE,
                "workflow_provenance": {"source": "google-flow-mcp", "engine_dir": str(flow.engine_dir()),
                                        "approval": approval},
                "provenance": {"source": "user_google_flow_account", "generator": "google_flow_image",
                               "third_party_audio": False, "license": IMAGE_LICENSE},
            },
            artifacts=[str(delivered)] + [str(p) for p in copies],
            cost_usd=0.0,
            duration_seconds=round(time.time() - start, 2),
            model="google-flow-image",
        )

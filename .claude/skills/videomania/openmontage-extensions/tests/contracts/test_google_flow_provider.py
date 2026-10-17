"""Google Flow provider contract: discovered, honest status, and never spends without approval.

No network and no real generation — the approval gate is the whole point, so a test that
let a stubbed job through would be testing nothing.
"""

from __future__ import annotations

from tools import _google_flow_client as flow

PROVIDER_TOOLS = ("google_flow_video", "google_flow_image")


def _stub_live_engine(monkeypatch, calls: list) -> None:
    monkeypatch.setattr(flow, "installed", lambda: True)
    monkeypatch.setattr(flow, "session_state", lambda **kw: {"available": True, "detail": "stubbed"})

    def _submit(kind, prompt, **kw):
        calls.append((kind, prompt))
        return {"jobId": "00000000-0000-0000-0000-000000000000", "status": "QUEUED"}

    monkeypatch.setattr(flow, "submit", _submit)


def test_flow_providers_are_discovered():
    from tools.tool_registry import registry

    registry.discover()
    for name in PROVIDER_TOOLS:
        tool = registry._tools.get(name)
        assert tool is not None, f"{name} is not registered"
        info = tool.get_info()
        assert info["provider"] == "google_flow"
        assert info["status"] in {"available", "degraded", "unavailable"}
        assert info["install_instructions"], f"{name} must tell the agent how to install the engine"


def test_no_engine_installed_means_unavailable(monkeypatch):
    from tools.graphics.google_flow_image import GoogleFlowImage
    from tools.video.google_flow_video import GoogleFlowVideo

    monkeypatch.setattr(flow, "installed", lambda: False)
    assert GoogleFlowVideo().get_status().value == "unavailable"
    assert GoogleFlowImage().get_status().value == "unavailable"


def test_generation_refuses_without_an_approval_quote(monkeypatch):
    from tools.graphics.google_flow_image import GoogleFlowImage
    from tools.video.google_flow_video import GoogleFlowVideo

    calls: list = []
    _stub_live_engine(monkeypatch, calls)

    for tool in (GoogleFlowVideo(), GoogleFlowImage()):
        result = tool.execute({"prompt": "a red fox turning to camera in mist"})
        assert result.success is False, f"{tool.name} submitted a paid job with no approval"
        assert "approval" in (result.error or "").lower()
    assert calls == [], "a paid generation was submitted without user approval"


def test_approval_quote_is_carried_into_provenance(monkeypatch, tmp_path):
    from tools.video.google_flow_video import GoogleFlowVideo

    calls: list = []
    _stub_live_engine(monkeypatch, calls)
    monkeypatch.setattr(flow, "wait", lambda job, **kw: {**job, "status": "COMPLETED", "events": []})

    engine_file = tmp_path / "final" / "video.mp4"
    engine_file.parent.mkdir(parents=True)
    engine_file.write_bytes(b"\x00" * 2048)
    monkeypatch.setattr(flow, "delivery_path", lambda job: engine_file)

    target = tmp_path / "assets" / "S02_plate.mp4"
    result = GoogleFlowVideo().execute(
        {"prompt": "a red fox turning to camera", "approval": "user approved G1", "output_path": str(target)}
    )

    assert result.success, result.error
    assert calls == [("video", "a red fox turning to camera")]
    assert result.data["approval"] == "user approved G1"
    assert result.data["provenance"]["source"] == "user_google_flow_account"
    assert target.is_file() and target.read_bytes() == engine_file.read_bytes()

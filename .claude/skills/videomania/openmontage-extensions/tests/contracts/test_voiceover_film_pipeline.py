"""Contracts for the voiceover-film pipeline and its local audio tools."""

from __future__ import annotations

import hashlib
from pathlib import Path

from lib.checkpoint import _stage_requires_approval, get_pipeline_stages
from lib.pipeline_loader import load_pipeline

REPO = Path(__file__).resolve().parents[2]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_manifest_loads_with_declared_order_and_gates() -> None:
    m = load_pipeline("voiceover-film")
    assert get_pipeline_stages("voiceover-film") == [
        "idea", "script", "scene_plan", "assets", "edit", "compose", "publish"]
    # Creative gates stay binding even though the pipeline is built for auto runs.
    for stage in ("idea", "scene_plan", "assets"):
        assert _stage_requires_approval("voiceover-film", stage) is True
    for stage in m["stages"]:
        assert (REPO / "skills" / f"{stage['skill']}.md").is_file()


def test_executive_producer_scopes_preauthorization() -> None:
    body = (REPO / "skills/pipelines/voiceover-film/executive-producer.md").read_text(encoding="utf-8")
    assert "approval_policy" in body
    assert "Does NOT cover paid generation" in body


def test_local_audio_tools_are_discovered() -> None:
    from tools.tool_registry import registry
    registry.discover()
    for name in ("procedural_score", "procedural_sfx"):
        info = registry._tools[name].get_info()
        assert info["status"] == "available"
        assert registry._tools[name].estimate_cost({}) == 0.0
    assert registry._tools["procedural_score"].capability == "music_generation"


def test_procedural_score_is_deterministic_and_tempo_fits(tmp_path: Path) -> None:
    from tools.audio.procedural_score import ProceduralScore
    args = {"duration_seconds": 6, "mood": "cinematic_minimal", "anchors": [3.0], "seed": 5,
            "sections": [{"start": 0, "end": 3, "role": "problem", "energy": 0.3},
                         {"start": 3, "end": 6, "role": "reveal", "energy": 0.8}]}
    a = ProceduralScore().execute({**args, "output_path": str(tmp_path / "a.wav")})
    b = ProceduralScore().execute({**args, "output_path": str(tmp_path / "b.wav")})
    assert a.success and b.success, (a.error, b.error)
    assert _sha(tmp_path / "a.wav") == _sha(tmp_path / "b.wav")
    assert min(abs(d - 3.0) for d in a.data["downbeats"]) < 0.08
    assert a.data["provenance"]["third_party_audio"] is False


def test_procedural_sfx_deterministic(tmp_path: Path) -> None:
    from tools.audio.procedural_sfx import ProceduralSFX
    cues = [{"time": 0.5, "type": "tick"}, {"time": 1.5, "type": "whoosh"}, {"time": 2.5, "type": "impact"}]
    for name in ("a", "b"):
        r = ProceduralSFX().execute({"output_path": str(tmp_path / f"{name}.wav"), "duration_seconds": 4, "cues": cues})
        assert r.success, r.error
    assert _sha(tmp_path / "a.wav") == _sha(tmp_path / "b.wav")
    bad = ProceduralSFX().execute({"output_path": str(tmp_path / "c.wav"), "duration_seconds": 2,
                                   "cues": [{"time": 0.1, "type": "laser"}]})
    assert not bad.success


def test_subtitle_gen_sentence_breaks_are_opt_in() -> None:
    from tools.subtitle.subtitle_gen import SubtitleGen
    words = [{"word": w, "start": i * 0.3, "end": i * 0.3 + 0.25} for i, w in
             enumerate(["One", "step.", "Then", "ship", "it."])]
    seg = [{"start": 0, "end": 1.5, "text": "", "words": words}]
    tool = SubtitleGen()
    legacy = tool._build_cues(seg, 8, 42)
    assert len(legacy) == 1  # default behaviour unchanged
    split = tool._build_cues(seg, 8, 42, break_on_sentence=True)
    assert [c["text"] for c in split] == ["One step.", "Then ship it."]

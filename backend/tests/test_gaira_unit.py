"""Unit tests for GAIRA parser and scoring engine."""

from pathlib import Path

from app.services.gaira.engine import (
    compute_ai_risk_levels,
    compute_gaira_light_routing,
    normalize_risk_level,
)
from app.services.gaira.framework import get_gaira_framework
from app.services.gaira.parser import parse_gaira_file, write_framework


def test_parse_gaira_source_has_core_modules():
    source = Path(__file__).resolve().parents[2] / "GAIRA" / "Rosenthal_GAIRA.json"
    if not source.exists():
        return
    framework = parse_gaira_file(source)
    modules = framework["modules"]
    assert "ai_risk_levels" in modules
    assert "gaira_light" in modules
    assert "ai_act_four_questions" not in modules
    assert len(modules["ai_risk_levels"]["questions"]) >= 20
    assert len(modules["gaira_light"]["questions"]) >= 100


def test_write_framework_creates_bundled_file(tmp_path):
    source = Path(__file__).resolve().parents[2] / "GAIRA" / "Rosenthal_GAIRA.json"
    if not source.exists():
        return
    output = tmp_path / "framework_v1.json"
    framework = write_framework(source, output)
    assert output.exists()
    assert framework["modules"]["gaira_light"]["key"] == "gaira_light"


def test_ai_risk_levels_high_when_step2_hit():
    framework = get_gaira_framework()
    questions = framework.questions_for_module("ai_risk_levels")
    step2_id = next(q["id"] for q in questions if q.get("step_id") == "2")
    result = compute_ai_risk_levels({step2_id: {"value": "Yes"}}, questions)
    assert result.risk_level == "high"
    assert result.recommended_module == "gaira_comprehensive"


def test_gaira_light_routing_recommends_comprehensive():
    result = compute_gaira_light_routing({"3.06": {"value": "Yes"}})
    assert result.recommended_module == "gaira_comprehensive"
    assert "routing_comprehensive" in result.flags


def test_normalize_risk_level():
    assert normalize_risk_level("Very high") == "very_high"
    assert normalize_risk_level("low") == "low"

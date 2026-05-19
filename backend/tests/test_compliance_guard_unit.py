"""Unit tests for compliance guard enforcement engine."""

from app.services.guard.runtime_enforcement_engine import RuntimeEnforcementEngine


def test_merge_block_wins_over_warn():
    engine = RuntimeEnforcementEngine()
    decision, score, level, blocking, warnings, _ = engine.merge(
        scan_decision="warn",
        scan_risk_score=40,
        scan_risk_level="medium",
        scan_reasons=["PII in prompt"],
        scan_source="prompt",
        rule_decision="block",
        rule_risk_score=80,
        rule_reasons=["Rule triggered"],
        policy_decision="allow",
    )
    assert decision == "block"
    assert "Rule triggered" in blocking


def test_merge_scan_block_only():
    engine = RuntimeEnforcementEngine()
    decision, _, _, blocking, _, _ = engine.merge(
        scan_decision="block",
        scan_risk_score=90,
        scan_risk_level="critical",
        scan_reasons=["API key detected"],
        scan_source="prompt",
    )
    assert decision == "block"
    assert blocking == ["API key detected"]

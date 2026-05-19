"""Backward-compatible helpers. Prefer ComplianceScoringEngine."""

from app.services.scanner.types import DetectionResult
from app.services.scoring.engine import ComplianceScoringEngine

_engine = ComplianceScoringEngine()


def compute_risk_score(findings: list[DetectionResult]) -> int:
    return _engine.score(findings).risk_score


def compliance_status(risk_score: int) -> str:
    if risk_score <= _engine.config.compliant_max:
        return "compliant"
    if risk_score <= _engine.config.risky_max:
        return "risky"
    return "non_compliant"


def classify_dataset(findings: list[DetectionResult], risk_score: int) -> str:
    return _engine.score(findings).classification

"""Risk scoring for prompt scan findings."""

from app.services.execution.constants import RISK_LEVEL_ORDER
from app.services.prompts.constants import RISK_SCORE_MAX, SEVERITY_WEIGHTS
from app.services.prompts.types import PromptFinding


def score_findings(findings: list[PromptFinding]) -> tuple[int, str]:
    if not findings:
        return 0, "low"

    total = 0
    max_severity = "low"
    for finding in findings:
        total += SEVERITY_WEIGHTS.get(finding.severity, 10)
        if RISK_LEVEL_ORDER.get(finding.severity, 0) > RISK_LEVEL_ORDER.get(max_severity, 0):
            max_severity = finding.severity

    score = min(RISK_SCORE_MAX, total)
    risk_level = _score_to_level(score, max_severity)
    return score, risk_level


def _score_to_level(score: int, max_severity: str) -> str:
    if score >= 70 or max_severity == "critical":
        return "critical"
    if score >= 40 or max_severity == "high":
        return "high"
    if score >= 20 or max_severity == "medium":
        return "medium"
    return "low"

from app.services.execution.constants import RISK_LEVEL_ORDER
from app.services.outputs.constants import RISK_SCORE_MAX, SEVERITY_WEIGHTS
from app.services.outputs.types import OutputFinding


def score_findings(findings: list[OutputFinding]) -> tuple[int, str]:
    if not findings:
        return 0, "low"

    total = 0
    max_severity = "low"
    for finding in findings:
        total += SEVERITY_WEIGHTS.get(finding.severity, 10)
        if RISK_LEVEL_ORDER.get(finding.severity, 0) > RISK_LEVEL_ORDER.get(max_severity, 0):
            max_severity = finding.severity

    score = min(RISK_SCORE_MAX, total)
    if score >= 70 or max_severity == "critical":
        return score, "critical"
    if score >= 40 or max_severity == "high":
        return score, "high"
    if score >= 20 or max_severity == "medium":
        return score, "medium"
    return score, "low"

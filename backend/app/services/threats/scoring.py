"""Threat score calculation."""

from app.services.threats.constants import SEVERITY_BASE_SCORE


def compute_threat_score(severity: str, recurrence_count: int = 1) -> int:
    base = SEVERITY_BASE_SCORE.get(severity, 50)
    boost = min(15, max(0, recurrence_count - 1) * 5)
    return min(100, base + boost)


def aggregate_security_posture(threats: list) -> int:
    """0-100 security posture (100 = best)."""
    if not threats:
        return 100
    avg = sum(t.threat_score for t in threats) / len(threats)
    return max(0, int(100 - avg * 0.65))

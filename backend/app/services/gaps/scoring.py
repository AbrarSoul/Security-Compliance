"""Severity scoring for compliance gaps."""

from app.services.gaps.constants import SEVERITY_SCORES


def score_for_severity(severity: str) -> int:
    return SEVERITY_SCORES.get(severity, 50)


def aggregate_run_score(gaps: list) -> int:
    """Overall posture score 0-100 (100 = best). Penalize by open gap scores."""
    if not gaps:
        return 100
    penalty = sum(min(g.score, 100) for g in gaps) / len(gaps)
    return max(0, int(100 - penalty * 0.6))

"""Unit tests for gap scoring and fingerprints."""

from uuid import uuid4

from app.services.gaps.constants import SEVERITY_CRITICAL, SEVERITY_HIGH
from app.services.gaps.scoring import aggregate_run_score, score_for_severity
from app.services.gaps.types import GapFinding


def test_score_for_severity():
    assert score_for_severity(SEVERITY_CRITICAL) > score_for_severity(SEVERITY_HIGH)


def test_aggregate_run_score_empty():
    assert aggregate_run_score([]) == 100


def test_gap_fingerprint_stable():
    uid = uuid4()
    f = GapFinding(
        gap_type="inactive_policy",
        category="governance",
        severity="high",
        title="T",
        description="D",
        recommendation="R",
        resource_type="compliance_policy",
        resource_id=uid,
    )
    assert f.fingerprint() == f"inactive_policy:compliance_policy:{uid}"

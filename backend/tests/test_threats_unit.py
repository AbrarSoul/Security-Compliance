"""Unit tests for threat scoring and fingerprints."""

from uuid import uuid4

from app.services.threats.constants import SEVERITY_CRITICAL, SEVERITY_HIGH
from app.services.threats.scoring import aggregate_security_posture, compute_threat_score
from app.services.threats.types import ThreatFinding


def test_compute_threat_score_recurrence():
    base = compute_threat_score(SEVERITY_HIGH, 1)
    boosted = compute_threat_score(SEVERITY_HIGH, 5)
    assert boosted > base


def test_aggregate_posture_empty():
    assert aggregate_security_posture([]) == 100


def test_threat_fingerprint():
    uid = uuid4()
    f = ThreatFinding(
        threat_type="prompt_injection_attack",
        category="prompt_security",
        severity=SEVERITY_CRITICAL,
        title="T",
        description="D",
        user_id=uid,
    )
    assert str(uid) in f.fingerprint()

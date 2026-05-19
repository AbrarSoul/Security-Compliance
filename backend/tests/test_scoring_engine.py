from app.services.scanner.types import DetectionResult
from app.services.scoring.config import ScoringConfig
from app.services.scoring.engine import ComplianceScoringEngine


def _config(**overrides) -> ScoringConfig:
    defaults = dict(
        severity_weights={"low": 5, "medium": 15, "high": 25, "critical": 40},
        finding_type_weights={
            "email": 10,
            "phone": 10,
            "password": 35,
            "api_key": 40,
            "name": 5,
            "sensitive_field": 8,
        },
        compliant_max=30,
        risky_max=60,
        score_max=100,
        density_multiplier=10,
        classification_restricted_min=70,
        classification_confidential_min=40,
        classification_internal_min=15,
        critical_escalation_match_rate=0.01,
        force_non_compliant_on_critical=True,
    )
    defaults.update(overrides)
    return ScoringConfig(**defaults)


def test_empty_findings_compliant():
    engine = ComplianceScoringEngine(_config())
    result = engine.score([])
    assert result.risk_score == 0
    assert result.compliance_status == "compliant"
    assert result.classification == "public"


def test_low_risk_compliant():
    engine = ComplianceScoringEngine(_config())
    findings = [DetectionResult("name", "low", "notes", 2, 0.1, {})]
    result = engine.score(findings)
    assert result.compliance_status == "compliant"
    assert result.risk_score <= 30


def test_medium_risk_risky():
    engine = ComplianceScoringEngine(_config())
    findings = [
        DetectionResult("email", "medium", "email", 50, 0.8, {}),
        DetectionResult("phone", "medium", "phone", 40, 0.7, {}),
    ]
    result = engine.score(findings)
    assert result.risk_score > 30
    assert result.compliance_status in ("risky", "non_compliant")
    assert result.classification == "confidential"


def test_critical_forces_non_compliant():
    engine = ComplianceScoringEngine(_config())
    findings = [DetectionResult("password", "critical", "password", 10, 1.0, {})]
    result = engine.score(findings)
    assert result.compliance_status == "non_compliant"
    assert result.classification == "restricted"
    assert any(a["type"] == "critical_escalation" for a in result.adjustments)


def test_high_score_non_compliant():
    engine = ComplianceScoringEngine(_config(compliant_max=10, risky_max=20))
    findings = [
        DetectionResult("api_key", "critical", "secret", 5, 1.0, {}),
        DetectionResult("password", "critical", "pwd", 5, 1.0, {}),
    ]
    result = engine.score(findings)
    assert result.risk_score > 20
    assert result.compliance_status == "non_compliant"


def test_score_capped_at_max():
    engine = ComplianceScoringEngine(_config(score_max=50))
    findings = [
        DetectionResult("api_key", "critical", "k", 100, 1.0, {}),
        DetectionResult("password", "critical", "p", 100, 1.0, {}),
    ]
    result = engine.score(findings)
    assert result.risk_score == 50


def test_breakdown_serialization():
    engine = ComplianceScoringEngine(_config())
    findings = [DetectionResult("email", "medium", "email", 5, 0.5, {})]
    result = engine.score(findings)
    breakdown = result.to_breakdown_dict()
    assert breakdown["compliance_status"] == result.compliance_status
    assert len(breakdown["contributions"]) == 1
    assert breakdown["contributions"][0]["total_points"] > 0


def test_configurable_thresholds():
    engine = ComplianceScoringEngine(_config(compliant_max=5, risky_max=15))
    findings = [DetectionResult("email", "medium", "email", 5, 0.5, {})]
    result = engine.score(findings)
    # medium(15) + density(5) + email(10) = 30 > 15
    assert result.compliance_status == "non_compliant"

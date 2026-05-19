from app.services.recommendations import RecommendationEngine
from app.services.scanner.types import DetectionResult
from app.services.scoring.engine import ComplianceScoringEngine


def test_email_recommendation():
    findings = [DetectionResult("email", "medium", "email", 50, 0.9, {})]
    recs = RecommendationEngine().generate(findings)
    assert len(recs) >= 1
    email_rec = next(r for r in recs if r.finding_type == "email")
    assert email_rec.action_type == "anonymize"
    assert email_rec.priority == "medium"
    assert "email" in email_rec.description.lower()


def test_password_recommendation_high_priority():
    findings = [DetectionResult("password", "critical", "user_password", 10, 1.0, {})]
    recs = RecommendationEngine().generate(findings)
    pwd_rec = next(r for r in recs if r.finding_type == "password")
    assert pwd_rec.priority == "high"
    assert pwd_rec.action_type == "remove_column"


def test_non_compliant_status_recommendations():
    findings = [
        DetectionResult("password", "critical", "pwd", 5, 1.0, {}),
        DetectionResult("api_key", "critical", "key", 2, 1.0, {}),
    ]
    score = ComplianceScoringEngine().score(findings)
    recs = RecommendationEngine().generate(findings, score)
    actions = {r.action_type for r in recs}
    assert "restrict_access" in actions
    assert "review_policy" in actions


def test_deduplicates_per_column():
    findings = [DetectionResult("email", "medium", "email", 10, 0.5, {})]
    recs = RecommendationEngine().generate(findings)
    email_recs = [r for r in recs if r.finding_type == "email"]
    assert len(email_recs) == 1


def test_empty_findings_compliant():
    score = ComplianceScoringEngine().score([])
    recs = RecommendationEngine().generate([], score)
    assert recs == []


def test_restricted_classification_encrypt_recommendation():
    findings = [DetectionResult("api_key", "critical", "secret", 1, 1.0, {})]
    score = ComplianceScoringEngine().score(findings)
    recs = RecommendationEngine().generate(findings, score)
    assert any(r.action_type == "encrypt" for r in recs)
    assert any(r.action_type == "rotate_secret" for r in recs)


def test_sorted_by_priority():
    findings = [
        DetectionResult("name", "low", "notes", 5, 0.2, {}),
        DetectionResult("password", "critical", "pwd", 5, 1.0, {}),
    ]
    recs = RecommendationEngine().generate(findings)
    assert recs[0].priority == "high"

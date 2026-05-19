from app.services.scanner.scanner import ComplianceScanner


def test_scanner_detects_email_and_phone():
    content = b"email,phone\nalice@example.com,+1-555-123-4567\nbob@test.org,5559876543\n"
    scanner = ComplianceScanner()
    findings = scanner.scan_content("csv", content)
    types = {f.finding_type for f in findings}
    assert "email" in types
    assert "phone" in types


def test_scanner_detects_password_column():
    content = b"user,password\nadmin,Str0ng!Pass\n"
    findings = ComplianceScanner().scan_content("csv", content)
    types = {f.finding_type for f in findings}
    assert "password" in types


def test_scanner_detects_api_key_column():
    content = b"id,api_key\n1,sk-live-abcdefghijklmnopqrstuvwxyz123456\n"
    findings = ComplianceScanner().scan_content("csv", content)
    types = {f.finding_type for f in findings}
    assert "api_key" in types


def test_scanner_detects_sensitive_field_column():
    content = b"ssn,notes\n123-45-6789,note\n"
    findings = ComplianceScanner().scan_content("csv", content)
    types = {f.finding_type for f in findings}
    assert "sensitive_field" in types


def test_scanner_json_array():
    content = b'[{"email": "a@b.com", "secret_key": "sk-test-abc123xyz789secretkeyval"}]'
    findings = ComplianceScanner().scan_content("json", content)
    types = {f.finding_type for f in findings}
    assert "email" in types


def test_risk_scorer():
    from app.services.scanner.types import DetectionResult
    from app.services.scoring import ComplianceScoringEngine

    findings = [
        DetectionResult("email", "medium", "email", 10, 0.9, {}),
        DetectionResult("password", "critical", "pwd", 2, 1.0, {}),
    ]
    result = ComplianceScoringEngine().score(findings)
    assert result.risk_score > 0
    assert result.compliance_status == "non_compliant"
    assert result.classification == "restricted"

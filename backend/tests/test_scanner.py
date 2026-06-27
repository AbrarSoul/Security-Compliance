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


def test_scanner_ignores_quiz_content_columns():
    """Education/quiz datasets should not be flagged as password columns."""
    content = b"""[
        {
            "image": "https://cdn.example.com/bangabandhu.jpg",
            "options": "[\\"1920\\", \\"1971\\", \\"1947\\"]",
            "text": "Bangabandhu er jonmo kobe?",
            "text_en": "In which year was Bangabandhu born?"
        },
        {
            "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
            "options": "[\\"Option A\\", \\"Option B\\"]",
            "text": "Muktijuddho kobe shuru hoy?",
            "text_en": "When did the Liberation War start in 1971?"
        }
    ]"""
    findings = ComplianceScanner().scan_content("json", content)
    types = {f.finding_type for f in findings}
    assert "password" not in types


def test_scanner_detects_real_password_values_without_column_hint():
    content = b"id,credential\n1,MyS3cret!Key9\n2,AnotherP@ss1\n"
    findings = ComplianceScanner().scan_content("csv", content)
    pwd = [f for f in findings if f.finding_type == "password"]
    assert len(pwd) == 1
    assert pwd[0].column_name == "credential"


def test_scanner_password_column_requires_credential_like_values():
    content = b"password,notes\nhttps://example.com/login,general note\n"
    findings = ComplianceScanner().scan_content("csv", content)
    types = {f.finding_type for f in findings}
    assert "password" not in types


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


def test_scanner_records_csv_row_locations():
    content = (
        b"email,phone\n"
        b"alice@example.com,+1-555-123-4567\n"
        b"bob@test.org,5559876543\n"
        b"carol@example.org,+1-555-999-8888\n"
    )
    findings = ComplianceScanner().scan_content("csv", content)
    email = next(f for f in findings if f.finding_type == "email")
    locations = email.evidence["locations"]
    assert [loc["index"] for loc in locations] == [2, 3, 4]
    assert all("preview" in loc for loc in locations)


def test_scanner_records_json_record_locations():
    content = b"""[
        {"email": "not-an-email", "note": "plain"},
        {"email": "a@b.com", "note": "has email"},
        {"email": "c@d.org", "note": "also email"}
    ]"""
    findings = ComplianceScanner().scan_content("json", content)
    email = next(f for f in findings if f.finding_type == "email")
    assert email.evidence["location_type"] == "record"
    assert [loc["index"] for loc in email.evidence["locations"]] == [2, 3]


def test_scanner_password_locations():
    content = b"id,credential\n1,MyS3cret!Key9\n2,AnotherP@ss1\n"
    findings = ComplianceScanner().scan_content("csv", content)
    pwd = next(f for f in findings if f.finding_type == "password")
    assert [loc["index"] for loc in pwd.evidence["locations"]] == [2, 3]


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

"""Unit tests for rule matching and analysis scoring."""

from __future__ import annotations

import json

import pytest

from app.services.files.analysis import FileAnalysisEngine, FileRuleMatcher, compute_scores
from app.services.files.analysis.types import AnalysisFinding


@pytest.fixture
def engine() -> FileAnalysisEngine:
    return FileAnalysisEngine()


def test_rule_matcher_loads_editable_rules():
    matcher = FileRuleMatcher()
    rules = matcher.rules
    assert len(rules) >= 10
    assert all(r.get("rule_kind") == "risk" for r in rules)
    assert all("id" in r and "match" in r for r in rules)


def test_csv_password_column_rule(engine: FileAnalysisEngine):
    content = b"user,password\nalice,secret123\n"
    _, report = engine.analyze_content("csv", content, file_name="users.csv")
    password_finding = next(f for f in report.findings if f.rule_id == "col_password_field")
    assert password_finding.matched
    detections = engine.analysis_findings_to_detections(report.findings)
    assert any(d.finding_type == "rule_col_password_field" for d in detections)


def test_clean_csv_no_issues(engine: FileAnalysisEngine):
    content = b"user,name\nalice,Alice\n"
    _, report = engine.analyze_content("csv", content, file_name="users.csv")
    assert not any(f.matched for f in report.findings)
    assert engine.analysis_findings_to_detections(report.findings) == []
    assert report.risk_score == 0


def test_missing_values_detection_has_row_locations(engine: FileAnalysisEngine):
    content = b"name,email\nAlice,\nBob,\n"
    _, report = engine.analyze_content("csv", content, file_name="data.csv")
    detections = engine.analysis_findings_to_detections(report.findings)
    email_det = next(d for d in detections if d.column_name == "email")
    assert email_det.evidence["locations"]
    assert email_det.evidence["locations"][0]["index"] == 2
    assert email_det.column_name == "email"


def test_csv_empty_dataset_risk(engine: FileAnalysisEngine):
    content = b"name,email\n"
    _, report = engine.analyze_content("csv", content, file_name="empty.csv")
    empty_rule = next(f for f in report.findings if f.rule_id == "dq_empty_dataset")
    assert empty_rule.matched
    assert empty_rule.rule_kind == "risk"
    detections = engine.analysis_findings_to_detections(report.findings)
    assert any(d.finding_type == "rule_dq_empty_dataset" for d in detections)


def test_clean_txt_no_issues(engine: FileAnalysisEngine):
    content = b"hello world\n"
    _, report = engine.analyze_content("txt", content, file_name="notes.txt")
    assert not any(f.matched for f in report.findings)
    assert engine.analysis_findings_to_detections(report.findings) == []


def test_log_auth_failure_rule(engine: FileAnalysisEngine):
    content = b"2024-01-01 ERROR authentication failed for user admin\n"
    _, report = engine.analyze_content("log", content, file_name="app.log")
    auth = next(f for f in report.findings if f.rule_id == "log_auth_failures")
    assert auth.matched
    assert auth.evidence.get("findings")


def test_scoring_risk_only_clean():
    findings = [
        AnalysisFinding(
            rule_id="password_col",
            rule_name="Password column",
            category="security",
            severity="critical",
            matched=False,
            required=False,
            rule_kind="risk",
            message="ok",
            explanation="no password column",
        ),
    ]
    compliance, risk, matched, missing, high_missing = compute_scores(findings)
    assert matched == 1
    assert missing == 0
    assert risk == 0
    assert compliance == 100


def test_scoring_risk_detected():
    findings = [
        AnalysisFinding(
            rule_id="password_col",
            rule_name="Password column",
            category="security",
            severity="critical",
            matched=True,
            required=False,
            rule_kind="risk",
            message="found",
            explanation="password column present",
        ),
    ]
    compliance, risk, matched, missing, high_missing = compute_scores(findings)
    assert matched == 0
    assert risk > 0


def test_report_shape(engine: FileAnalysisEngine):
    content = json.dumps([{"name": "Alice", "role": "analyst"}]).encode()
    _, report = engine.analyze_content("json", content, file_id=42, file_name="data.json")
    data = report.to_dict()
    assert data["file_id"] == "42"
    assert data["file_name"] == "data.json"
    assert isinstance(data["findings"], list)

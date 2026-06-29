"""Scoring for file analysis reports."""

from __future__ import annotations

from app.services.files.analysis.types import AnalysisFinding, FileAnalysisReport

_HIGH_RISK_SEVERITIES = frozenset({"critical", "high"})
_SEVERITY_RISK_WEIGHTS = {
    "critical": 15,
    "high": 10,
    "medium": 5,
    "low": 2,
}


def compute_scores(findings: list[AnalysisFinding]) -> tuple[int, int, int, int, int]:
    """
    Return (compliance_score, risk_score, matched_rules, missing_rules, high_risk_missing).

    For compliance_score, "matched" means satisfied:
    - requirement rules: matched = satisfied
    - risk rules: not matched = satisfied (no risk found)
    """
    if not findings:
        return 100, 0, 0, 0, 0

    def is_satisfied(f: AnalysisFinding) -> bool:
        if f.rule_kind == "requirement":
            return f.matched
        return not f.matched

    total = len(findings)
    satisfied = sum(1 for f in findings if is_satisfied(f))
    missing = total - satisfied

    required_findings = [f for f in findings if f.required]
    required_satisfied = sum(1 for f in required_findings if is_satisfied(f))
    required_total = len(required_findings)

    compliance_score = 100
    if total > 0:
        compliance_score = int(round((satisfied / total) * 100))
    if required_total > 0:
        required_compliance = int(round((required_satisfied / required_total) * 100))
        compliance_score = min(compliance_score, required_compliance)

    high_risk_missing = sum(
        1 for f in findings
        if f.rule_kind == "requirement"
        and f.required
        and not f.matched
        and f.severity in _HIGH_RISK_SEVERITIES
    )

    risk_score = 0
    for finding in findings:
        if finding.rule_kind == "risk" and finding.matched:
            if finding.category in {"security", "operations", "data_quality", "privacy"}:
                risk_score += _SEVERITY_RISK_WEIGHTS.get(finding.severity, 5)
        if finding.rule_kind == "requirement" and finding.required and not finding.matched:
            risk_score += _SEVERITY_RISK_WEIGHTS.get(finding.severity, 5)

    risk_score = min(risk_score, 100)
    matched = satisfied
    return compliance_score, risk_score, matched, missing, high_risk_missing


def build_report(
    *,
    file_id,
    file_name: str,
    findings: list[AnalysisFinding],
    extraction_summary: dict | None = None,
) -> FileAnalysisReport:
    compliance_score, risk_score, matched, missing, high_risk_missing = compute_scores(findings)
    return FileAnalysisReport(
        file_id=file_id,
        file_name=file_name,
        compliance_score=compliance_score,
        risk_score=risk_score,
        total_rules=len(findings),
        matched_rules=matched,
        missing_rules=missing,
        high_risk_missing=high_risk_missing,
        findings=findings,
        extraction_summary=extraction_summary or {},
    )

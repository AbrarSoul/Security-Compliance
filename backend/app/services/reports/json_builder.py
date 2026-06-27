from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.services.reports.summary_text import build_executive_narrative, format_issue_summary


def _iso(dt) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.astimezone(UTC).isoformat()
    return str(dt)


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    return float(value)


def build_report_json(
    *,
    report_id: UUID,
    scan,
    file_record,
    file_metadata,
) -> dict[str, Any]:
    """Assemble the full compliance report document as a JSON-serializable dict."""
    findings = scan.findings or []
    recommendations = scan.recommendations or []
    score_breakdown = scan.score_breakdown_json or {}

    severities = [f.severity for f in findings]
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    highest_severity = (
        max(severities, key=lambda s: severity_order.get(s, 0)) if severities else None
    )

    duration_ms = None
    if scan.started_at and scan.completed_at:
        duration_ms = int((scan.completed_at - scan.started_at).total_seconds() * 1000)

    file_info = {
        "id": str(file_record.id),
        "name": file_record.original_name,
        "file_type": file_record.file_type,
        "size_bytes": file_record.size_bytes,
        "row_count": file_metadata.row_count if file_metadata else None,
        "column_count": file_metadata.column_count if file_metadata else None,
    }

    detected_issues = [
        {
            "id": str(f.id),
            "type": f.finding_type,
            "severity": f.severity,
            "column": f.column_name,
            "sample_count": f.sample_count,
            "match_rate": _float_or_none(f.match_rate),
            "evidence": f.evidence_json,
        }
        for f in findings
    ]
    for issue in detected_issues:
        issue["summary"] = format_issue_summary(issue)

    narrative = build_executive_narrative(
        compliance_status=scan.compliance_status,
        classification=scan.classification,
        risk_score=scan.risk_score,
        findings=detected_issues,
        file_info=file_info,
    )

    return {
        "report_id": str(report_id),
        "scan_id": str(scan.id),
        "generated_at": datetime.now(UTC).isoformat(),
        "file": file_info,
        "executive_summary": {
            "risk_score": scan.risk_score,
            "compliance_status": scan.compliance_status,
            "classification": scan.classification,
            "total_findings": len(findings),
            "highest_severity": highest_severity,
            "headline": narrative["headline"],
            "detail": narrative["detail"],
            "scan_scope": narrative["scan_scope"],
        },
        "scan_summary": {
            "status": scan.status,
            "started_at": _iso(scan.started_at),
            "completed_at": _iso(scan.completed_at),
            "duration_ms": duration_ms,
            "findings_count": len(findings),
            "recommendations_count": len(recommendations),
            "methodology": "Sample-based column pattern scan (row limit configured server-side)",
        },
        "detected_issues": detected_issues,
        "recommendations": [
            {
                "id": str(r.id),
                "priority": r.priority,
                "title": r.title,
                "description": r.description,
                "action_type": r.action_type,
                "finding_type": r.finding_type,
                "column": r.column_name,
            }
            for r in recommendations
        ],
        "compliance_score": {
            "risk_score": scan.risk_score,
            "status": scan.compliance_status,
            "classification": scan.classification,
            "breakdown": score_breakdown,
        },
    }

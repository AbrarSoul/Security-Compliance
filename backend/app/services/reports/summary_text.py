"""Human-readable executive summary text for compliance reports."""

from typing import Any

FINDING_LABELS: dict[str, str] = {
    "email": "email addresses",
    "phone": "phone numbers",
    "password": "plaintext credentials",
    "api_key": "API keys or secrets",
    "name": "personal names",
    "sensitive_field": "sensitive personal data",
}

REASON_LABELS: dict[str, str] = {
    "credential_like_values_detected": "credential-like value patterns",
    "password_column_with_credential_like_values": "password-related column naming and values",
    "sensitive_column_name": "sensitive column naming",
    "name_pattern_in_values": "person-name patterns in values",
    "column_name_indicates_password_storage": "password-related column naming",
}


def _finding_label(finding_type: str) -> str:
    return FINDING_LABELS.get(finding_type, finding_type.replace("_", " "))


def _reason_label(reason: str | None) -> str | None:
    if not reason:
        return None
    return REASON_LABELS.get(reason, reason.replace("_", " "))


def build_executive_narrative(
    *,
    compliance_status: str | None,
    classification: str | None,
    risk_score: int | None,
    findings: list[Any],
    file_info: dict[str, Any],
) -> dict[str, str]:
    """Return headline + detail paragraphs for report consumers."""
    status = compliance_status or "unknown"
    total = len(findings)

    if total == 0:
        headline = "No sensitive data patterns detected"
        detail = (
            f"A sample-based scan of '{file_info.get('name', 'the dataset')}' "
            f"did not identify email addresses, credentials, API keys, or other "
            f"high-risk sensitive patterns in the analyzed rows."
        )
    elif status == "compliant":
        headline = "Dataset appears compliant with low residual risk"
        types = sorted({_finding_label(f.get("type") or getattr(f, "finding_type", "")) for f in findings})
        detail = (
            f"The scan found {total} low-impact pattern(s) ({', '.join(types)}). "
            "Risk remains within compliant thresholds, but review recommendations before external sharing."
        )
    elif status == "risky":
        headline = "Dataset requires review before production use"
        types = sorted({_finding_label(f.get("type") or getattr(f, "finding_type", "")) for f in findings})
        detail = (
            f"{total} finding(s) were identified ({', '.join(types)}). "
            "Sensitive patterns are present at moderate levels. Remediate or apply controls before wider distribution."
        )
    else:
        headline = "Dataset is not compliant — immediate remediation recommended"
        critical = [
            f for f in findings
            if (f.get("severity") if isinstance(f, dict) else getattr(f, "severity", "")) == "critical"
        ]
        types = sorted({_finding_label(f.get("type") or getattr(f, "finding_type", "")) for f in findings})
        crit_note = f" including {len(critical)} critical" if critical else ""
        detail = (
            f"The scan identified {total} finding(s){crit_note} across {', '.join(types)}. "
            "Do not share or process this dataset in production until remediation is complete."
        )

    scope_parts: list[str] = []
    if file_info.get("file_type"):
        scope_parts.append(str(file_info["file_type"]).upper())
    if file_info.get("row_count") is not None:
        scope_parts.append(f"{file_info['row_count']:,} rows profiled")
    if file_info.get("column_count") is not None:
        scope_parts.append(f"{file_info['column_count']} columns")
    scope = " · ".join(scope_parts) if scope_parts else "Sample-based column scan"

    score_note = ""
    if risk_score is not None:
        if risk_score <= 30:
            band = "low"
        elif risk_score <= 60:
            band = "moderate"
        else:
            band = "high"
        score_note = f" Risk score {risk_score}/100 ({band})."
    if classification:
        score_note += f" Data classification: {classification}."

    return {
        "headline": headline,
        "detail": detail + score_note,
        "scan_scope": scope,
    }


def _location_type_label(location_type: str | None) -> str:
    return {
        "row": "Row",
        "record": "Record",
        "line": "Line",
        "field": "Field",
    }.get(location_type or "", "Row")


def format_location_list(evidence: dict[str, Any] | None) -> str | None:
    """Compact location string for reports, e.g. 'Rows 2, 5, 9 (+3 more)'."""
    if not evidence:
        return None
    locations = evidence.get("locations") or []
    if not locations:
        return None
    label = _location_type_label(evidence.get("location_type"))
    plural = {"Row": "Rows", "Record": "Records", "Line": "Lines", "Field": "Fields"}.get(
        label, label + "s"
    )
    indices = [str(loc.get("index")) for loc in locations if loc.get("index") is not None]
    if not indices:
        return None
    extra = evidence.get("additional_match_count") or 0
    count_label = label if len(indices) == 1 else plural
    base = f"{count_label} {', '.join(indices)}"
    if extra:
        base += f" (+{extra} more)"
    return base


def format_issue_summary(issue: dict[str, Any]) -> str:
    """One-line human summary for a detected issue."""
    label = _finding_label(issue.get("type", ""))
    column = issue.get("column")
    evidence = issue.get("evidence") or {}
    reason = _reason_label(evidence.get("reason"))
    match_rate = issue.get("match_rate")
    location_str = format_location_list(evidence)
    parts = [label]
    if column:
        parts.append(f"in column '{column}'")
    if location_str:
        parts.append(f"at {location_str}")
    if reason:
        parts.append(f"({reason})")
    if match_rate is not None:
        parts.append(f"— {match_rate * 100:.1f}% of sampled rows")
    return " ".join(parts)

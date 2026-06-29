"""Orchestrate extraction, rule matching, and scoring."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from app.services.files.analysis.rule_matcher import FileRuleMatcher
from app.services.files.analysis.scorer import build_report
from app.services.files.analysis.types import AnalysisFinding, FileAnalysisReport
from app.services.files.extraction.service import extract_file
from app.services.files.extraction.types import ExtractedContent
from app.services.scanner.types import DetectionResult


class FileAnalysisEngine:
    """Deterministic, explainable file analysis (no LLM)."""

    def __init__(self, rules_path: Path | None = None):
        self.matcher = FileRuleMatcher()
        if rules_path is not None:
            self.matcher.reload_rules(rules_path)

    def reload_rules(self, rules_path: Path | None = None) -> None:
        self.matcher.reload_rules(rules_path)

    def extract(self, file_type: str, content: bytes) -> ExtractedContent:
        return extract_file(file_type, content)

    def analyze_content(
        self,
        file_type: str,
        content: bytes,
        *,
        file_id: UUID | int | None = None,
        file_name: str = "upload",
        risk_only: bool = True,
    ) -> tuple[ExtractedContent, FileAnalysisReport]:
        extracted = self.extract(file_type, content)
        findings = self.matcher.evaluate(extracted)
        if risk_only:
            findings = [f for f in findings if f.rule_kind == "risk"]
        summary = self._extraction_summary(extracted)
        report = build_report(
            file_id=file_id,
            file_name=file_name,
            findings=findings,
            extraction_summary=summary,
        )
        return extracted, report

    def analysis_findings_to_detections(
        self, findings: list[AnalysisFinding]
    ) -> list[DetectionResult]:
        """Convert matched *risk* rules into scanner-compatible detections."""
        detections: list[DetectionResult] = []
        for finding in findings:
            if finding.rule_kind != "risk" or not finding.matched:
                continue
            if finding.category == "structure" and finding.severity == "low":
                continue

            if finding.rule_id in {"dq_missing_values", "dq_duplicate_rows"}:
                sub_findings = finding.evidence.get("findings") or []
                if sub_findings:
                    detections.extend(
                        _detections_from_data_quality_subfindings(finding, sub_findings)
                    )
                    continue

            sample_count = _risk_sample_count(finding)
            evidence = _build_rule_evidence(finding)
            detections.append(
                DetectionResult(
                    finding_type=f"rule_{finding.rule_id}",
                    severity=finding.severity,
                    column_name=_risk_column_name(finding),
                    sample_count=sample_count,
                    match_rate=1.0 if sample_count > 0 else 0.0,
                    evidence=evidence,
                )
            )
        return detections

    def gap_findings(self, findings: list[AnalysisFinding]) -> list[AnalysisFinding]:
        """Required *requirement* rules that were not satisfied — compliance gaps."""
        return [
            f for f in findings
            if f.rule_kind == "requirement" and f.required and not f.matched
        ]

    @staticmethod
    def _extraction_summary(extracted: ExtractedContent) -> dict[str, Any]:
        return {
            "file_type": extracted.file_type,
            "text_block_count": len(extracted.text_blocks),
            "table_count": len(extracted.tables),
            "record_count": len(extracted.records),
            "structure": {
                "headings": len(extracted.structure.get("headings", [])),
                "sections": len(extracted.structure.get("sections", [])),
                "pages": len(extracted.structure.get("pages", [])),
                "sheets": len(extracted.structure.get("sheets", [])),
            },
            "data_quality": extracted.data_quality,
        }


def _build_rule_evidence(finding: AnalysisFinding) -> dict[str, Any]:
    evidence = {
        "finding_kind": "risk",
        "rule_id": finding.rule_id,
        "rule_name": finding.rule_name,
        "message": finding.message,
        "explanation": finding.explanation,
        **finding.evidence,
    }
    if "locations" not in evidence and "matches" in evidence:
        matches = evidence.get("matches") or []
        evidence["location_type"] = evidence.get("location_type", "line")
        evidence["locations"] = [
            {
                "index": m.get("line") or m.get("page") or m.get("paragraph_index"),
                "preview": m.get("snippet") or m.get("match"),
                "column": m.get("column"),
            }
            for m in matches
            if isinstance(m, dict)
        ][:10]
    return evidence


def _detections_from_data_quality_subfindings(
    parent: AnalysisFinding,
    sub_findings: list[dict[str, Any]],
) -> list[DetectionResult]:
    results: list[DetectionResult] = []
    for sub in sub_findings:
        sub_evidence = sub.get("evidence") or {}
        locations = sub_evidence.get("locations") or []
        column = sub.get("column")
        count = int(
            sub_evidence.get("missing_count")
            or sub_evidence.get("duplicate_count")
            or len(locations)
            or 1
        )
        results.append(
            DetectionResult(
                finding_type=f"rule_{parent.rule_id}",
                severity=str(sub.get("severity", parent.severity)),
                column_name=str(column) if column else None,
                sample_count=count,
                match_rate=round(count / max(count, 1), 4),
                evidence={
                    "finding_kind": "risk",
                    "rule_id": parent.rule_id,
                    "rule_name": sub.get("message") or parent.rule_name,
                    "message": sub.get("message") or parent.message,
                    "explanation": sub.get("message") or parent.explanation,
                    "issue_type": sub.get("type"),
                    **sub_evidence,
                },
            )
        )
    return results


def _risk_sample_count(finding: AnalysisFinding) -> int:
    evidence = finding.evidence or {}
    if "count" in evidence:
        return int(evidence["count"])
    if "findings" in evidence and isinstance(evidence["findings"], list):
        return len(evidence["findings"])
    if "matches" in evidence and isinstance(evidence["matches"], list):
        return len(evidence["matches"])
    if "columns" in evidence and isinstance(evidence["columns"], list):
        return len(evidence["columns"])
    if "keyword_hits" in evidence and isinstance(evidence["keyword_hits"], list):
        return len(evidence["keyword_hits"])
    return 1


def _risk_column_name(finding: AnalysisFinding) -> str | None:
    evidence = finding.evidence or {}
    columns = evidence.get("columns")
    if isinstance(columns, list) and columns:
        return str(columns[0])
    column = evidence.get("column")
    if column:
        return str(column)
    return None

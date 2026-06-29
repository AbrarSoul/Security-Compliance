"""Types for explainable file analysis reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


# requirement: file must satisfy this (gap when not matched)
# risk: match indicates a problem (issue when matched)
RuleKind = str  # "requirement" | "risk"


@dataclass
class AnalysisFinding:
    rule_id: str
    rule_name: str
    category: str
    severity: str
    matched: bool
    required: bool
    rule_kind: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "category": self.category,
            "severity": self.severity,
            "matched": self.matched,
            "required": self.required,
            "rule_kind": self.rule_kind,
            "message": self.message,
            "evidence": self.evidence,
            "explanation": self.explanation,
        }


@dataclass
class FileAnalysisReport:
    file_id: UUID | int | None
    file_name: str
    compliance_score: int
    risk_score: int
    total_rules: int
    matched_rules: int
    missing_rules: int
    high_risk_missing: int
    findings: list[AnalysisFinding] = field(default_factory=list)
    extraction_summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_id": str(self.file_id) if self.file_id is not None else None,
            "file_name": self.file_name,
            "compliance_score": self.compliance_score,
            "risk_score": self.risk_score,
            "total_rules": self.total_rules,
            "matched_rules": self.matched_rules,
            "missing_rules": self.missing_rules,
            "high_risk_missing": self.high_risk_missing,
            "findings": [f.to_dict() for f in self.findings],
            "extraction_summary": self.extraction_summary,
        }

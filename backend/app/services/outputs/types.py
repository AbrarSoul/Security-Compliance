from dataclasses import dataclass, field
from typing import Any


@dataclass
class OutputFinding:
    finding_type: str
    severity: str
    message: str
    matched_span: str | None = None
    masked_span: str | None = None
    suggested_decision: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_type": self.finding_type,
            "severity": self.severity,
            "message": self.message,
            "matched_span": self.matched_span,
            "masked_span": self.masked_span,
            "suggested_decision": self.suggested_decision,
            "evidence": self.evidence,
        }


@dataclass
class OutputScanOutcome:
    decision: str
    risk_score: int
    risk_level: str
    findings: list[OutputFinding] = field(default_factory=list)
    masked_output: str = ""
    redacted_output: str = ""
    blocking_reasons: list[str] = field(default_factory=list)
    warning_reasons: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    can_display: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "findings": [f.to_dict() for f in self.findings],
            "masked_output": self.masked_output,
            "redacted_output": self.redacted_output,
            "blocking_reasons": self.blocking_reasons,
            "warning_reasons": self.warning_reasons,
            "recommendations": self.recommendations,
            "can_display": self.can_display,
        }

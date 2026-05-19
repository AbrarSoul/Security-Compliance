from dataclasses import dataclass, field
from typing import Any, Literal

ComplianceStatus = Literal["compliant", "risky", "non_compliant"]
DataClassification = Literal["public", "internal", "confidential", "restricted"]
RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass
class FindingContribution:
    finding_type: str
    severity: RiskLevel
    column_name: str | None
    base_points: int
    density_points: int
    type_weight_points: int
    total_points: int
    match_rate: float


@dataclass
class ComplianceScoreResult:
    risk_score: int
    compliance_status: ComplianceStatus
    classification: DataClassification
    highest_severity: RiskLevel | None
    total_findings: int
    contributions: list[FindingContribution] = field(default_factory=list)
    adjustments: list[dict[str, Any]] = field(default_factory=list)
    thresholds_applied: dict[str, int] = field(default_factory=dict)

    def to_breakdown_dict(self) -> dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "compliance_status": self.compliance_status,
            "classification": self.classification,
            "highest_severity": self.highest_severity,
            "total_findings": self.total_findings,
            "contributions": [
                {
                    "finding_type": c.finding_type,
                    "severity": c.severity,
                    "column_name": c.column_name,
                    "base_points": c.base_points,
                    "density_points": c.density_points,
                    "type_weight_points": c.type_weight_points,
                    "total_points": c.total_points,
                    "match_rate": c.match_rate,
                }
                for c in self.contributions
            ],
            "adjustments": self.adjustments,
            "thresholds_applied": self.thresholds_applied,
        }

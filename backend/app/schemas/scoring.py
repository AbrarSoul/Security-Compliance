from typing import Any

from pydantic import BaseModel, Field


class ComplianceThresholdsResponse(BaseModel):
    compliant_max: int = Field(description="Risk score at or below this is compliant")
    risky_max: int = Field(description="Risk score at or below this is risky (above = non-compliant)")
    score_max: int = Field(description="Maximum possible risk score")


class ClassificationThresholdsResponse(BaseModel):
    restricted_min: int
    confidential_min: int
    internal_min: int


class ScoringRulesResponse(BaseModel):
    density_multiplier: int
    critical_escalation_match_rate: float
    force_non_compliant_on_critical: bool


class ScoringConfigResponse(BaseModel):
    severity_weights: dict[str, int]
    finding_type_weights: dict[str, int]
    compliance_thresholds: ComplianceThresholdsResponse
    classification_thresholds: ClassificationThresholdsResponse
    rules: ScoringRulesResponse


class FindingContributionResponse(BaseModel):
    finding_type: str
    severity: str
    column_name: str | None
    base_points: int
    density_points: int
    type_weight_points: int
    total_points: int
    match_rate: float


class ComplianceScoreResponse(BaseModel):
    risk_score: int
    compliance_status: str
    classification: str
    highest_severity: str | None
    total_findings: int
    contributions: list[FindingContributionResponse] = []
    adjustments: list[dict[str, Any]] = []
    thresholds_applied: dict[str, int] = {}

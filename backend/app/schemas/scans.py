from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.recommendations import RecommendationResponse
from app.schemas.rules import RuleEvaluationResponse
from app.schemas.scoring import ComplianceScoreResponse


class CreateScanRequest(BaseModel):
    file_id: UUID


class ScanFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    finding_type: str
    severity: str
    column_name: str | None
    sample_count: int
    match_rate: float | None
    evidence: dict[str, Any] | None = Field(
        validation_alias="evidence_json", serialization_alias="evidence"
    )
    created_at: datetime


class ScanSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    status: str
    risk_score: int | None
    compliance_status: str | None
    classification: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    findings_count: int | None = None


class ScanDetailResponse(ScanSummaryResponse):
    findings: list[ScanFindingResponse] = []
    recommendations: list[RecommendationResponse] = []
    compliance_score: ComplianceScoreResponse | None = Field(
        default=None,
        description="Detailed scoring breakdown when scan is completed",
    )
    rule_evaluation: RuleEvaluationResponse | None = Field(
        default=None,
        description="Database-driven rule engine evaluation when scan is completed",
    )


class ScanListResponse(BaseModel):
    items: list[ScanSummaryResponse]
    total: int
    limit: int
    offset: int

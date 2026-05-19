"""Compliance gap analysis API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComplianceGapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    analysis_run_id: UUID
    gap_type: str
    category: str
    severity: str
    score: int
    title: str
    description: str
    recommendation: str
    status: str
    fingerprint: str
    resource_type: str | None
    resource_id: UUID | None
    metadata_json: dict | None
    detected_at: datetime
    resolved_at: datetime | None


class GapAnalysisRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    triggered_by_user_id: UUID | None
    scope: str
    gaps_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    summary_json: dict | None
    started_at: datetime
    completed_at: datetime | None


class GapAnalysisRunDetailResponse(GapAnalysisRunResponse):
    gaps: list[ComplianceGapResponse] = Field(default_factory=list)
    posture_score: int | None = None


class GapListResponse(BaseModel):
    items: list[ComplianceGapResponse]
    total: int
    limit: int
    offset: int
    latest_run_id: UUID | None = None
    posture_score: int | None = None


class GapRunListResponse(BaseModel):
    items: list[GapAnalysisRunResponse]
    total: int
    limit: int
    offset: int


class GapDashboardResponse(BaseModel):
    latest_run: GapAnalysisRunResponse | None
    open_gaps: list[ComplianceGapResponse]
    open_total: int
    by_severity: dict[str, int]
    by_category: dict[str, int]
    posture_score: int
    last_analyzed_at: datetime | None

"""Threat detection API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SecurityThreatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    detection_run_id: UUID | None
    user_id: UUID | None
    threat_type: str
    category: str
    severity: str
    threat_score: int
    title: str
    description: str
    status: str
    fingerprint: str
    source_event_type: str | None
    session_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    metadata_json: dict | None
    detected_at: datetime
    resolved_at: datetime | None


class SecurityEventLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    threat_id: UUID | None
    event_type: str
    threat_type: str | None
    severity: str
    message: str
    payload_json: dict | None
    created_at: datetime


class ThreatDetectionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    triggered_by_user_id: UUID | None
    threats_found: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    summary_json: dict | None
    started_at: datetime
    completed_at: datetime | None


class ThreatRunDetailResponse(ThreatDetectionRunResponse):
    threats: list[SecurityThreatResponse] = Field(default_factory=list)


class ThreatDashboardResponse(BaseModel):
    open_threats: list[SecurityThreatResponse]
    open_total: int
    by_severity: dict[str, int]
    by_type: dict[str, int]
    security_posture: int
    latest_run: ThreatDetectionRunResponse | None


class UserBehaviorItem(BaseModel):
    user_id: str
    threat_count: int
    avg_threat_score: float
    risk_level: str


class UserBehaviorResponse(BaseModel):
    items: list[UserBehaviorItem]


class ThreatListResponse(BaseModel):
    items: list[SecurityThreatResponse]
    total: int
    limit: int
    offset: int


class SecurityEventListResponse(BaseModel):
    items: list[SecurityEventLogResponse]
    total: int
    limit: int
    offset: int

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MonitoringSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    execution_request_id: UUID | None
    status: str
    event_count: int
    alert_count: int
    last_risk_score: int | None
    last_event_type: str | None
    metadata_json: dict[str, Any] | None
    opened_at: datetime
    closed_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class MonitoringSessionListResponse(BaseModel):
    items: list[MonitoringSessionResponse]
    total: int
    limit: int
    offset: int


class OpenMonitoringSessionRequest(BaseModel):
    execution_request_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class PublishMonitoringEventRequest(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=128)
    session_id: UUID | None = None
    payload: dict[str, Any] | None = None
    severity: str = Field(default="info", max_length=16)
    resource_type: str | None = Field(default=None, max_length=64)
    resource_id: UUID | None = None
    correlation_id: UUID | None = None
    source: str = Field(default="api", max_length=32)


class DomainEventResponse(BaseModel):
    id: UUID
    event_type: str
    user_id: UUID | None
    session_id: UUID | None
    correlation_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    severity: str
    source: str
    payload_json: dict[str, Any] | None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class DomainEventListResponse(BaseModel):
    items: list[DomainEventResponse]
    total: int
    limit: int
    offset: int


class MonitoringStatusResponse(BaseModel):
    active_sessions: int
    total_events_today_hint: int | None = None
    outbox_pending: int | None = None
    outbox_worker_enabled: bool | None = None
    outbox_poll_seconds: float | None = None

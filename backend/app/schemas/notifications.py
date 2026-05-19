"""Notification API schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    notification_type: str
    severity: str
    title: str
    message: str
    event_type: str | None
    resource_type: str | None
    resource_id: UUID | None
    metadata_json: dict | None
    is_read: bool
    read_at: datetime | None
    email_status: str | None
    email_sent_at: datetime | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int


class MarkReadResponse(BaseModel):
    id: UUID
    is_read: bool
    read_at: datetime | None


class MarkAllReadResponse(BaseModel):
    updated: int


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    in_app_enabled: bool
    email_enabled: bool
    email_min_severity: str
    dashboard_alerts_enabled: bool
    notify_prompt_blocked: bool
    notify_output_blocked: bool
    notify_policy_violation: bool
    notify_suspicious_activity: bool
    notify_high_risk_execution: bool
    notify_repeated_violation: bool
    notify_system_security: bool
    updated_at: datetime


class NotificationPreferenceUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    email_min_severity: str | None = Field(default=None, pattern="^(info|warning|high|critical)$")
    dashboard_alerts_enabled: bool | None = None
    notify_prompt_blocked: bool | None = None
    notify_output_blocked: bool | None = None
    notify_policy_violation: bool | None = None
    notify_suspicious_activity: bool | None = None
    notify_high_risk_execution: bool | None = None
    notify_repeated_violation: bool | None = None
    notify_system_security: bool | None = None

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: UUID | None
    severity: str | None
    status: str
    ip_address: str | None
    user_agent: str | None
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    request_id: str | None
    created_at: datetime
    actor_email: str | None = None

    @classmethod
    def from_model(cls, row) -> "AuditLogResponse":
        actor_email = row.user.email if getattr(row, "user", None) else None
        return cls(
            id=row.id,
            user_id=row.user_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            severity=row.severity,
            status=row.status,
            ip_address=row.ip_address,
            user_agent=row.user_agent,
            metadata=row.metadata_json,
            request_id=row.request_id,
            created_at=row.created_at,
            actor_email=actor_email,
        )


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    limit: int
    offset: int

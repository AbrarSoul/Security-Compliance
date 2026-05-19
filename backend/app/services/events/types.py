"""Domain event envelope for the monitoring pipeline."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass
class DomainEventEnvelope:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    user_id: UUID | None = None
    correlation_id: UUID | None = None
    session_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    severity: str = "info"
    source: str = "api"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "user_id": str(self.user_id) if self.user_id else None,
            "correlation_id": str(self.correlation_id) if self.correlation_id else None,
            "session_id": str(self.session_id) if self.session_id else None,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "severity": self.severity,
            "source": self.source,
            "payload": self.payload,
        }

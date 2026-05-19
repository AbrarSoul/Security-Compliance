"""Threat finding types."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class ThreatFinding:
    threat_type: str
    category: str
    severity: str
    title: str
    description: str
    user_id: UUID | None = None
    source_event_type: str | None = None
    session_id: UUID | None = None
    resource_type: str | None = None
    resource_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    recurrence_count: int = 1

    def fingerprint(self) -> str:
        uid = str(self.user_id) if self.user_id else "global"
        rid = str(self.resource_id) if self.resource_id else "none"
        return f"{self.threat_type}:{uid}:{rid}"

"""Gap finding types for the analysis engine."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class GapFinding:
    gap_type: str
    category: str
    severity: str
    title: str
    description: str
    recommendation: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        rid = str(self.resource_id) if self.resource_id else "global"
        return f"{self.gap_type}:{self.resource_type or 'none'}:{rid}"

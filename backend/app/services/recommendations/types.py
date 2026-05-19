from dataclasses import dataclass, field
from typing import Any, Literal

Priority = Literal["low", "medium", "high"]
ActionType = Literal[
    "remove_column",
    "anonymize",
    "mask",
    "encrypt",
    "rotate_secret",
    "restrict_access",
    "review_policy",
    "audit_logging",
]


@dataclass
class RecommendationResult:
    priority: Priority
    title: str
    description: str
    action_type: ActionType
    finding_type: str | None = None
    column_name: str | None = None
    related_finding_types: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

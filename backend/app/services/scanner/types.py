from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnSample:
    name: str
    values: list[str]


@dataclass
class DetectionResult:
    finding_type: str
    severity: str
    column_name: str | None
    sample_count: int
    match_rate: float
    evidence: dict[str, Any] = field(default_factory=dict)

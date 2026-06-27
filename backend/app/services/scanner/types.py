from dataclasses import dataclass, field
from typing import Any, Literal

LocationType = Literal["row", "record", "line", "field"]

MAX_LOCATIONS_IN_EVIDENCE = 5


@dataclass
class CellValue:
    """A single sampled cell with a 1-based display index (row, record, or line)."""

    index: int
    value: str


@dataclass
class ColumnSample:
    name: str
    cells: list[CellValue]
    location_type: LocationType = "row"

    @property
    def values(self) -> list[str]:
        return [c.value for c in self.cells]


@dataclass
class DetectionResult:
    finding_type: str
    severity: str
    column_name: str | None
    sample_count: int
    match_rate: float
    evidence: dict[str, Any] = field(default_factory=dict)

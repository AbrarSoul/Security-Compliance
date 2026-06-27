from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.location_evidence import collect_cell_evidence, collect_match_evidence
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()


def _normalize_column(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


class SensitiveFieldDetector:
    """Detects PII-related column names and person-name patterns in values."""

    name = "sensitive_field"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [c for c in column.cells if c.value]
        if not non_empty:
            return None

        normalized = _normalize_column(column.name)
        name_match = normalized in patterns.SENSITIVE_COLUMN_NAMES
        pattern_match = bool(patterns.SENSITIVE_COLUMN_PATTERNS.search(column.name))

        name_matches = [c for c in non_empty if patterns.NAME_VALUE_RE.match(c.value)]
        name_value_rate = len(name_matches) / len(non_empty)

        if name_match or pattern_match:
            return DetectionResult(
                finding_type="sensitive_field",
                severity="low" if normalized in ("email", "phone", "phone_number") else "medium",
                column_name=column.name,
                sample_count=len(non_empty),
                match_rate=1.0,
                evidence=collect_cell_evidence(
                    non_empty,
                    location_type=column.location_type,
                    extra={
                        "reason": "sensitive_column_name",
                        "column_indicator": normalized,
                    },
                ),
            )

        if name_value_rate >= settings.scan_match_threshold:
            return DetectionResult(
                finding_type="name",
                severity="low",
                column_name=column.name,
                sample_count=len(name_matches),
                match_rate=round(name_value_rate, 4),
                evidence=collect_match_evidence(
                    column,
                    patterns.NAME_VALUE_RE.match,
                    extra={"reason": "name_pattern_in_values"},
                ),
            )

        return None

from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()


def _normalize_column(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


class SensitiveFieldDetector:
    """Detects PII-related column names and person-name patterns in values."""

    name = "sensitive_field"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [v for v in column.values if v]
        if not non_empty:
            return None

        normalized = _normalize_column(column.name)
        name_match = normalized in patterns.SENSITIVE_COLUMN_NAMES
        pattern_match = bool(patterns.SENSITIVE_COLUMN_PATTERNS.search(column.name))

        name_value_hits = sum(1 for v in non_empty if patterns.NAME_VALUE_RE.match(v))
        name_value_rate = name_value_hits / len(non_empty)

        if name_match or pattern_match:
            return DetectionResult(
                finding_type="sensitive_field",
                severity="low" if normalized in ("email", "phone", "phone_number") else "medium",
                column_name=column.name,
                sample_count=len(non_empty),
                match_rate=1.0,
                evidence={
                    "reason": "sensitive_column_name",
                    "column_indicator": normalized,
                    "masked_samples": [patterns.mask_value(v) for v in non_empty[:3]],
                },
            )

        if name_value_rate >= settings.scan_match_threshold:
            return DetectionResult(
                finding_type="name",
                severity="low",
                column_name=column.name,
                sample_count=name_value_hits,
                match_rate=round(name_value_rate, 4),
                evidence={
                    "reason": "name_pattern_in_values",
                    "masked_samples": [patterns.mask_value(v) for v in non_empty if patterns.NAME_VALUE_RE.match(v)][:3],
                },
            )

        return None

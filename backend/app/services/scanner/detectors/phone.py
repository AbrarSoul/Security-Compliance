from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.location_evidence import collect_match_evidence
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()


def _is_phone(value: str) -> bool:
    if not patterns.PHONE_RE.match(value):
        return False
    digits = sum(1 for c in value if c.isdigit())
    return digits >= 10


class PhoneDetector:
    name = "phone"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [c for c in column.cells if c.value]
        if not non_empty:
            return None

        hits = sum(1 for c in non_empty if _is_phone(c.value))
        rate = hits / len(non_empty)
        if rate < settings.scan_match_threshold:
            return None

        return DetectionResult(
            finding_type="phone",
            severity="medium",
            column_name=column.name,
            sample_count=hits,
            match_rate=round(rate, 4),
            evidence=collect_match_evidence(column, _is_phone),
        )

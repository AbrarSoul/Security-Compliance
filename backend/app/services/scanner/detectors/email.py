from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()


class EmailDetector:
    name = "email"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [v for v in column.values if v]
        if not non_empty:
            return None

        hits = sum(1 for v in non_empty if patterns.EMAIL_RE.match(v))
        rate = hits / len(non_empty)
        if rate < settings.scan_match_threshold:
            return None

        return DetectionResult(
            finding_type="email",
            severity="medium",
            column_name=column.name,
            sample_count=hits,
            match_rate=round(rate, 4),
            evidence={
                "masked_samples": [patterns.mask_value(v) for v in _sample_matches(non_empty, patterns.EMAIL_RE)][:3],
            },
        )


def _sample_matches(values: list[str], pattern) -> list[str]:
    return [v for v in values if pattern.match(v)]

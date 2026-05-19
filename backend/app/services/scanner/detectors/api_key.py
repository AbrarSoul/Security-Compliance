from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()

API_KEY_COLUMN_HINTS = ("api_key", "apikey", "secret", "token", "access_key", "private_key")


def _is_api_key(value: str) -> bool:
    if patterns.API_KEY_RE.search(value):
        return True
    if patterns.STANDALONE_API_KEY_RE.match(value):
        return True
    return False


class ApiKeyDetector:
    name = "api_key"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [v for v in column.values if v]
        if not non_empty:
            return None

        col_lower = column.name.lower().replace("-", "_")
        column_hint = any(hint in col_lower for hint in API_KEY_COLUMN_HINTS)

        hits = sum(1 for v in non_empty if _is_api_key(v))
        rate = hits / len(non_empty) if non_empty else 0

        if column_hint and hits == 0 and len(non_empty) >= 1:
            # Long alphanumeric strings in secret columns
            plausible = sum(
                1 for v in non_empty if len(v) >= 20 and v.replace("_", "").replace("-", "").isalnum()
            )
            if plausible / len(non_empty) >= settings.scan_match_threshold:
                hits = plausible
                rate = plausible / len(non_empty)

        if hits == 0:
            return None

        if rate < settings.scan_match_threshold and not column_hint:
            return None

        return DetectionResult(
            finding_type="api_key",
            severity="critical",
            column_name=column.name,
            sample_count=hits,
            match_rate=round(max(rate, hits / len(non_empty)), 4),
            evidence={
                "masked_samples": [patterns.mask_value(v, visible=4) for v in non_empty if _is_api_key(v)][:3]
                or ["***"] * min(3, hits),
            },
        )

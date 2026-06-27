from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.location_evidence import collect_cell_evidence, collect_match_evidence
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()

API_KEY_COLUMN_HINTS = ("api_key", "apikey", "secret", "token", "access_key", "private_key")


def _is_api_key(value: str) -> bool:
    if patterns.API_KEY_RE.search(value):
        return True
    if patterns.STANDALONE_API_KEY_RE.match(value):
        return True
    return False


def _is_plausible_secret(value: str) -> bool:
    return len(value) >= 20 and value.replace("_", "").replace("-", "").isalnum()


class ApiKeyDetector:
    name = "api_key"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [c for c in column.cells if c.value]
        if not non_empty:
            return None

        col_lower = column.name.lower().replace("-", "_")
        column_hint = any(hint in col_lower for hint in API_KEY_COLUMN_HINTS)

        key_matches = [c for c in non_empty if _is_api_key(c.value)]
        hits = len(key_matches)
        rate = hits / len(non_empty) if non_empty else 0

        if column_hint and hits == 0 and non_empty:
            plausible_matches = [c for c in non_empty if _is_plausible_secret(c.value)]
            if len(plausible_matches) / len(non_empty) >= settings.scan_match_threshold:
                key_matches = plausible_matches
                hits = len(plausible_matches)
                rate = hits / len(non_empty)

        if hits == 0:
            return None

        if rate < settings.scan_match_threshold and not column_hint:
            return None

        if key_matches and any(_is_api_key(c.value) for c in key_matches):
            evidence = collect_match_evidence(
                column,
                _is_api_key,
                mask=lambda v: patterns.mask_value(v, visible=4),
            )
        else:
            evidence = collect_cell_evidence(
                key_matches,
                location_type=column.location_type,
                mask=lambda v: patterns.mask_value(v, visible=4),
            )

        return DetectionResult(
            finding_type="api_key",
            severity="critical",
            column_name=column.name,
            sample_count=hits,
            match_rate=round(max(rate, hits / len(non_empty)), 4),
            evidence=evidence,
        )

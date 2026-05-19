from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()

PASSWORD_COLUMN_HINTS = ("password", "passwd", "pwd", "secret")


class PasswordDetector:
    name = "password"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [v for v in column.values if v]
        if not non_empty:
            return None

        col_lower = column.name.lower().replace("-", "_")
        column_hint = any(hint in col_lower for hint in PASSWORD_COLUMN_HINTS)
        pattern_hits = sum(1 for v in non_empty if patterns.PASSWORD_RE.match(v))
        rate = pattern_hits / len(non_empty)

        if column_hint:
            return DetectionResult(
                finding_type="password",
                severity="critical",
                column_name=column.name,
                sample_count=max(pattern_hits, len(non_empty)),
                match_rate=round(max(rate, 1.0), 4),
                evidence={
                    "reason": "column_name_indicates_password_storage",
                    "masked_samples": ["***"] * min(3, len(non_empty)),
                },
            )

        if rate < settings.scan_match_threshold:
            return None

        return DetectionResult(
            finding_type="password",
            severity="critical",
            column_name=column.name,
            sample_count=pattern_hits,
            match_rate=round(rate, 4),
            evidence={"masked_samples": ["***"] * min(3, pattern_hits)},
        )

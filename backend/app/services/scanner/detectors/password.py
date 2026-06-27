from app.core.config import get_settings
from app.services.scanner import patterns
from app.services.scanner.location_evidence import collect_cell_evidence, collect_match_evidence
from app.services.scanner.types import ColumnSample, DetectionResult

settings = get_settings()

PASSWORD_COLUMN_HINTS = ("password", "passwd", "pwd", "user_password", "pass_hash")
CONTENT_COLUMN_BLOCKLIST = frozenset({
    "image", "images", "img", "picture", "photo", "avatar", "icon", "thumbnail",
    "banner", "logo", "media", "attachment", "file", "filename",
    "text", "title", "description", "content", "body", "message", "question",
    "answer", "options", "choices", "label", "caption", "summary", "excerpt",
    "html", "markdown", "code", "script", "data", "payload", "metadata",
    "config", "settings", "json", "xml", "yaml", "url", "link", "href", "src",
    "uri", "path", "notes", "comment", "comments", "tags", "category", "type",
    "status", "slug", "header", "footer", "paragraph", "sentence", "prompt",
})
PASSWORD_MATCH_THRESHOLD = 0.3


def _normalize_column(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_")


def _column_suggests_password(column_name: str) -> bool:
    col_lower = _normalize_column(column_name)
    return any(hint in col_lower for hint in PASSWORD_COLUMN_HINTS)


def _column_is_content_field(column_name: str) -> bool:
    col_lower = _normalize_column(column_name)
    if col_lower in CONTENT_COLUMN_BLOCKLIST:
        return True
    return any(
        col_lower.endswith(suffix)
        for suffix in ("_text", "_image", "_url", "_html", "_json", "_options")
    )


class PasswordDetector:
    name = "password"

    def detect(self, column: ColumnSample) -> DetectionResult | None:
        non_empty = [c for c in column.cells if c.value]
        if not non_empty:
            return None

        column_hint = _column_suggests_password(column.name)
        content_column = _column_is_content_field(column.name)

        if content_column and not column_hint:
            return None

        matches = [c for c in non_empty if patterns.looks_like_password(c.value)]
        rate = len(matches) / len(non_empty)

        if column_hint:
            if not matches:
                return None
            if rate < PASSWORD_MATCH_THRESHOLD:
                return None
            return DetectionResult(
                finding_type="password",
                severity="critical",
                column_name=column.name,
                sample_count=len(matches),
                match_rate=round(rate, 4),
                evidence=collect_cell_evidence(
                    matches,
                    location_type=column.location_type,
                    mask=lambda _v: "***",
                    extra={"reason": "password_column_with_credential_like_values"},
                ),
            )

        if rate < PASSWORD_MATCH_THRESHOLD:
            return None

        return DetectionResult(
            finding_type="password",
            severity="critical",
            column_name=column.name,
            sample_count=len(matches),
            match_rate=round(rate, 4),
            evidence=collect_match_evidence(
                column,
                patterns.looks_like_password,
                mask=lambda v: patterns.mask_value(v, visible=2),
                extra={"reason": "credential_like_values_detected"},
            ),
        )

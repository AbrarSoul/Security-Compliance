"""Mask sensitive substrings in prompt text for safe storage and display."""

import re

from app.services.prompts import patterns
from app.services.scanner.patterns import mask_value


def mask_prompt(text: str, *, max_length: int = 4000) -> str:
    """Apply layered masking for known secret/PII patterns."""
    if not text:
        return ""

    masked = text

    def _sub(pattern: re.Pattern[str], replacer):
        nonlocal masked
        masked = pattern.sub(replacer, masked)

    _sub(
        patterns.AWS_ACCESS_KEY_RE,
        lambda m: mask_value(m.group(0), visible=4),
    )
    _sub(
        patterns.AWS_SECRET_KEY_RE,
        lambda m: f"aws_secret_key=***{mask_value(m.group(1), visible=0)}",
    )
    _sub(
        patterns.API_KEY_ASSIGNMENT_RE,
        lambda m: mask_value(m.group(0), visible=6),
    )
    _sub(
        patterns.STANDALONE_API_KEY_RE,
        lambda m: mask_value(m.group(0), visible=4),
    )
    _sub(patterns.SSN_RE, lambda m: "***-**-****")
    _sub(
        patterns.CREDIT_CARD_RE,
        lambda m: mask_value(re.sub(r"\s", "", m.group(0)), visible=4),
    )
    _sub(
        patterns.EMAIL_IN_TEXT_RE,
        lambda m: mask_value(m.group(0), visible=2),
    )

    masked = re.sub(
        r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+",
        r"\1=***",
        masked,
    )

    if len(masked) > max_length:
        masked = masked[: max_length - 3] + "..."
    return masked

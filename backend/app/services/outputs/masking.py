"""Redact sensitive content in AI outputs with explicit mask tokens."""

import re

from app.services.outputs import patterns
from app.services.outputs.constants import (
    MASK_API_KEY,
    MASK_BANK,
    MASK_CONFIDENTIAL,
    MASK_CREDIT_CARD,
    MASK_EMAIL,
    MASK_HARMFUL,
    MASK_HEALTHCARE,
    MASK_PASSWORD,
    MASK_PHONE,
    MASK_SSN,
    MASK_TOXIC,
    MASKED_OUTPUT_MAX_STORE,
)


def mask_output(text: str, *, max_length: int = MASKED_OUTPUT_MAX_STORE) -> str:
    if not text:
        return ""

    masked = text

    def _sub(pattern: re.Pattern[str], replacement: str) -> None:
        nonlocal masked
        masked = pattern.sub(replacement, masked)

    _sub(patterns.AWS_ACCESS_KEY_RE, MASK_API_KEY)
    _sub(patterns.AWS_SECRET_KEY_RE, MASK_API_KEY)
    _sub(patterns.API_KEY_ASSIGNMENT_RE, MASK_API_KEY)
    _sub(patterns.STANDALONE_API_KEY_RE, MASK_API_KEY)
    _sub(patterns.SSN_RE, MASK_SSN)
    _sub(patterns.CREDIT_CARD_RE, MASK_CREDIT_CARD)
    _sub(patterns.EMAIL_IN_TEXT_RE, MASK_EMAIL)
    _sub(patterns.PHONE_IN_TEXT_RE, MASK_PHONE)

    masked = re.sub(
        r"(?i)(password|passwd|pwd)\s*[:=]\s*\S+",
        rf"\1={MASK_PASSWORD}",
        masked,
    )

    for harmful in patterns.HARMFUL_PATTERNS:
        masked = harmful.sub(MASK_HARMFUL, masked)
    for toxic in patterns.TOXIC_PATTERNS:
        masked = toxic.sub(MASK_TOXIC, masked)

    if len(masked) > max_length:
        masked = masked[: max_length - 3] + "..."
    return masked


def redact_for_display(text: str, findings: list) -> str:
    """Apply mask tokens; for block decisions caller may return empty instead."""
    return mask_output(text)

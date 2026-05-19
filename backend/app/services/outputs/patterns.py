"""Patterns for output leakage and unsafe content detection."""

import re

from app.services.prompts import patterns as prompt_patterns

# Reuse prompt-layer secret / PII patterns
EMAIL_IN_TEXT_RE = prompt_patterns.EMAIL_IN_TEXT_RE
PHONE_IN_TEXT_RE = prompt_patterns.PHONE_IN_TEXT_RE
SSN_RE = prompt_patterns.SSN_RE
PASSWORD_ASSIGN_RE = prompt_patterns.PASSWORD_ASSIGN_RE
PASSWORD_RE = prompt_patterns.PASSWORD_RE
API_KEY_ASSIGNMENT_RE = prompt_patterns.API_KEY_ASSIGNMENT_RE
STANDALONE_API_KEY_RE = prompt_patterns.STANDALONE_API_KEY_RE
AWS_ACCESS_KEY_RE = prompt_patterns.AWS_ACCESS_KEY_RE
AWS_SECRET_KEY_RE = prompt_patterns.AWS_SECRET_KEY_RE
CREDIT_CARD_RE = prompt_patterns.CREDIT_CARD_RE
CREDIT_CARD_CONTEXT_RE = prompt_patterns.CREDIT_CARD_CONTEXT_RE
BANK_ACCOUNT_RE = prompt_patterns.BANK_ACCOUNT_RE
BANK_CONTEXT_RE = prompt_patterns.BANK_CONTEXT_RE
FINANCIAL_KEYWORDS_RE = prompt_patterns.FINANCIAL_KEYWORDS_RE
HEALTHCARE_KEYWORDS_RE = prompt_patterns.HEALTHCARE_KEYWORDS_RE
CONFIDENTIAL_RE = prompt_patterns.CONFIDENTIAL_RE

BUSINESS_SENSITIVE_RE = re.compile(
    r"(?i)\b(revenue\s+target|merger\s+plan|acquisition\s+target|"
    r"layoff\s+list|executive\s+compensation|unreleased\s+earnings|"
    r"board\s+meeting\s+minutes|cap\s+table)\b"
)

HARMFUL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)\b(how\s+to|steps\s+to|instructions\s+to)\s+(make|build|construct)\s+(a\s+)?(bomb|explosive|weapon)\b"
    ),
    re.compile(r"(?i)\b(make|build|construct)\s+(a\s+)?(bomb|explosive|weapon)\b"),
    re.compile(r"(?i)\b(instructions|steps)\s+to\s+(harm|hurt|kill)\b"),
    re.compile(r"(?i)\bcommit\s+(suicide|self[- ]harm)\b"),
    re.compile(r"(?i)\b(synthesize|manufacture)\s+(meth|fentanyl|illegal\s+drugs)\b"),
    re.compile(r"(?i)\bdisable\s+(security|firewall|antivirus)\s+to\s+hack\b"),
)

TOXIC_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(you\s+are\s+)?(worthless|disgusting|subhuman)\b"),
    re.compile(r"(?i)\b(kill\s+yourself|kys)\b"),
    re.compile(r"(?i)\b(racial|ethnic)\s+slur\b"),
    re.compile(
        r"(?i)\b("
        r"fuck\s+you|"
        r"piece\s+of\s+shit|"
        r"damn\s+you"
        r")\b"
    ),
)

"""Regex and keyword patterns for real-time prompt scanning."""

import re

from app.services.scanner import patterns as scan_patterns

# Reuse dataset scanner patterns where applicable
EMAIL_RE = scan_patterns.EMAIL_RE
EMAIL_IN_TEXT_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)
PHONE_RE = scan_patterns.PHONE_RE
PHONE_IN_TEXT_RE = re.compile(r"\+?[\d\s\-().]{10,20}")
PASSWORD_RE = scan_patterns.PASSWORD_RE
PASSWORD_ASSIGN_RE = re.compile(
    r"(?i)(password|passwd|pwd)\s*[:=]\s*(\S{8,128})",
)
API_KEY_ASSIGNMENT_RE = scan_patterns.API_KEY_RE
STANDALONE_API_KEY_RE = scan_patterns.STANDALONE_API_KEY_RE

# Cloud provider secrets
AWS_ACCESS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
AWS_SECRET_KEY_RE = re.compile(
    r"(?i)aws[_\-]?(?:secret[_\-]?access[_\-]?)?key\s*[:=]\s*['\"]?([A-Za-z0-9/+=]{40})"
)
# PII
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SSN_CONTEXT_RE = re.compile(r"(?i)\b(ssn|social\s+security)\b")

# Financial
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
CREDIT_CARD_CONTEXT_RE = re.compile(r"(?i)\b(card|credit\s+card|cvv|visa|mastercard)\b")
BANK_ACCOUNT_RE = re.compile(r"\b\d{8,17}\b")
BANK_CONTEXT_RE = re.compile(r"(?i)\b(routing|iban|bank\s+account|account\s+number)\b")
FINANCIAL_KEYWORDS_RE = re.compile(
    r"(?i)\b(salary|payroll|wire\s+transfer|tax\s+id|ein|revenue\s+forecast|"
    r"profit\s+and\s+loss|balance\s+sheet)\b"
)

# Healthcare
HEALTHCARE_KEYWORDS_RE = re.compile(
    r"(?i)\b(patient\s+name|medical\s+record|mrn|hipaa|diagnosis|"
    r"prescription|icd-?\d{1,2}|phi|protected\s+health)\b"
)
DOB_CONTEXT_RE = re.compile(r"(?i)\b(date\s+of\s+birth|dob)\s*[:=]\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")

# Company confidential
CONFIDENTIAL_RE = re.compile(
    r"(?i)\b(confidential|internal\s+use\s+only|trade\s+secret|"
    r"proprietary|nda|not\s+for\s+distribution|company\s+secret)\b"
)

# Prompt injection
INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions"),
    re.compile(r"(?i)disregard\s+(your\s+)?(guidelines|instructions|rules|policy)"),
    re.compile(r"(?i)forget\s+(everything|all)\s+you\s+(were|have\s+been)\s+told"),
    re.compile(r"(?i)override\s+(the\s+)?(system|safety)\s+(prompt|instructions)"),
    re.compile(r"(?i)\bsystem\s*:\s*"),
    re.compile(r"(?i)reveal\s+(the\s+)?(system|hidden)\s+prompt"),
    re.compile(r"(?i)print\s+(your\s+)?(system|initial)\s+instructions"),
    re.compile(r"(?i)act\s+as\s+if\s+you\s+have\s+no\s+restrictions"),
)

# Jailbreak
JAILBREAK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\bDAN\b.*\bmode\b"),
    re.compile(r"(?i)do\s+anything\s+now"),
    re.compile(r"(?i)jailbreak"),
    re.compile(r"(?i)bypass\s+(safety|content)\s+(filter|policy|restrictions)"),
    re.compile(r"(?i)developer\s+mode\s+enabled"),
    re.compile(r"(?i)you\s+are\s+now\s+in\s+.*unrestricted"),
    re.compile(r"(?i)pretend\s+you\s+are\s+an?\s+evil"),
    re.compile(r"(?i)no\s+ethical\s+guidelines"),
)

# Suspicious instructions
SUSPICIOUS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)\b(exfiltrate|steal|dump)\s+(all\s+)?(data|database|credentials)"),
    re.compile(r"(?i)\bdisable\s+(logging|audit|monitoring)\b"),
    re.compile(r"(?i)\bsend\s+(all\s+)?(secrets|passwords|keys)\s+to\b"),
    re.compile(r"(?i)\bwrite\s+malware\b"),
    re.compile(r"(?i)\b(lateral\s+movement|privilege\s+escalation)\b"),
)

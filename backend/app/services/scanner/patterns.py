import re

EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
)
PHONE_RE = re.compile(
    r"^\+?[\d\s\-().]{10,20}$",
)
# Compact credential-like token: 8-72 chars, mixed character classes, no whitespace.
PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9\s])\S{8,72}$",
)
URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
DATA_URI_RE = re.compile(r"^data:", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[a-z][^>]*>", re.IGNORECASE)
JSON_STRUCTURE_RE = re.compile(r"^[\[{]|^\s*\{|\[\s*\"|\":\s*")
FILE_PATH_RE = re.compile(
    r"[/\\]|\.(?:png|jpe?g|gif|svg|webp|bmp|ico|json|xml|html?|pdf|csv|txt|md|yaml|yml)\b",
    re.IGNORECASE,
)
_BASE64_CHARSET = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
API_KEY_RE = re.compile(
    r"(?:api[_\-]?key|secret[_\-]?key|access[_\-]?token|auth[_\-]?token)"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})",
    re.IGNORECASE,
)
STANDALONE_API_KEY_RE = re.compile(
    r"^(?:sk|pk)[-_](?:live|test)[-_][A-Za-z0-9]{16,}$|^[A-Za-z0-9_\-]{32,64}$",
)
NAME_VALUE_RE = re.compile(
    r"^[A-Z][a-z]+(?:[\s\-'][A-Z][a-z]+)+$",
)

SENSITIVE_COLUMN_NAMES = frozenset({
    "name",
    "full_name",
    "firstname",
    "first_name",
    "lastname",
    "last_name",
    "customer_name",
    "user_name",
    "username",
    "email",
    "phone",
    "phone_number",
    "mobile",
    "ssn",
    "social_security",
    "social_security_number",
    "national_id",
    "passport",
    "dob",
    "date_of_birth",
    "birth_date",
    "address",
    "street",
    "home_address",
    "password",
    "passwd",
    "user_password",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "credit_card",
    "card_number",
    "cvv",
    "bank_account",
    "account_number",
    "salary",
    "income",
})

SENSITIVE_COLUMN_PATTERNS = re.compile(
    r"(password|secret|token|api[_\-]?key|ssn|social.?security|credit.?card|"
    r"bank.?account|passport|salary|confidential|private.?key)",
    re.IGNORECASE,
)


def _is_likely_base64(value: str) -> bool:
    stripped = value.strip()
    if len(stripped) < 32:
        return False
    if DATA_URI_RE.match(stripped):
        return True
    base64_chars = sum(1 for ch in stripped if ch in _BASE64_CHARSET)
    return base64_chars / len(stripped) >= 0.92


def _looks_like_natural_language(value: str) -> bool:
    if " " not in value:
        return False
    words = value.split()
    if len(words) < 2:
        return False
    alpha = sum(1 for ch in value if ch.isalpha())
    if alpha / max(len(value), 1) < 0.5:
        return False
    vowels = sum(1 for ch in value.lower() if ch in "aeiou")
    return vowels / max(alpha, 1) >= 0.28


def looks_like_password(value: str) -> bool:
    """Return True only when a value plausibly represents a stored plaintext password."""
    if not value:
        return False
    stripped = value.strip()
    if not PASSWORD_RE.match(stripped):
        return False
    if URL_RE.search(stripped):
        return False
    if DATA_URI_RE.match(stripped):
        return False
    if HTML_TAG_RE.search(stripped):
        return False
    if FILE_PATH_RE.search(stripped):
        return False
    if JSON_STRUCTURE_RE.search(stripped):
        return False
    if _is_likely_base64(stripped):
        return False
    if _looks_like_natural_language(stripped):
        return False
    return True


def mask_value(value: str, visible: int = 2) -> str:
    if len(value) <= visible * 2:
        return "***"
    return value[:visible] + "***" + value[-visible:]

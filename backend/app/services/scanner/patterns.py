import re

EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
)
PHONE_RE = re.compile(
    r"^\+?[\d\s\-().]{10,20}$",
)
# At least 8 chars with upper, lower, digit, special
PASSWORD_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,128}$",
)
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


def mask_value(value: str, visible: int = 2) -> str:
    if len(value) <= visible * 2:
        return "***"
    return value[:visible] + "***" + value[-visible:]

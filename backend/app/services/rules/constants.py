"""Rule engine enumerations and weights."""

RULE_CATEGORIES: frozenset[str] = frozenset(
    {"data", "model", "execution", "security", "privacy"}
)

RULE_SEVERITIES: frozenset[str] = frozenset({"low", "medium", "high", "critical"})

RULE_ACTIONS: frozenset[str] = frozenset({"allow", "warn", "block"})

SEVERITY_ORDER: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

ACTION_ORDER: dict[str, int] = {
    "allow": 0,
    "warn": 1,
    "block": 2,
}

SEVERITY_RISK_POINTS: dict[str, int] = {
    "low": 5,
    "medium": 15,
    "high": 30,
    "critical": 50,
}

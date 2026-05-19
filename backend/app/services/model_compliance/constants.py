"""Model compliance enumerations."""

MODEL_TYPES: frozenset[str] = frozenset(
    {
        "local_model",
        "external_api",
        "cloud_hosted",
        "open_source",
        "proprietary",
    }
)

RISK_LEVELS: frozenset[str] = frozenset({"low", "medium", "high", "critical"})

DECISIONS: frozenset[str] = frozenset({"allow", "warn", "block"})

SENSITIVE_FINDING_TYPES: frozenset[str] = frozenset(
    {"password", "api_key", "sensitive_field", "phone"}
)

HIGH_RISK_CLASSIFICATIONS: frozenset[str] = frozenset({"confidential", "restricted"})

UNKNOWN_PROVIDERS: frozenset[str] = frozenset({"", "unknown", "n/a", "na", "none"})

RISK_LEVEL_ORDER: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

DECISION_ORDER: dict[str, int] = {
    "allow": 0,
    "warn": 1,
    "block": 2,
}

RISK_POINTS: dict[str, int] = {
    "low": 10,
    "medium": 25,
    "high": 40,
    "critical": 60,
}

"""Policy management enumerations."""

POLICY_TYPES: frozenset[str] = frozenset(
    {"data_policy", "model_policy", "execution_policy", "security_policy"}
)

POLICY_STATUSES: frozenset[str] = frozenset({"draft", "active", "inactive", "archived"})

ACTIVE_POLICY_STATUS = "active"

"""Pre-execution validation constants."""

DECISIONS: frozenset[str] = frozenset({"allow", "warn", "block"})

DECISION_ORDER: dict[str, int] = {
    "allow": 0,
    "warn": 1,
    "block": 2,
}

RISK_LEVEL_ORDER: dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

# Lifecycle statuses (execution_requests.status)
STATUS_PENDING_VALIDATION = "pending_validation"
STATUS_ALLOWED = "allowed"
STATUS_WARNING_PENDING_ACK = "warning_pending_acknowledgement"
STATUS_APPROVED_AFTER_WARNING = "approved_after_warning"
STATUS_BLOCKED = "blocked"
STATUS_STARTED = "started"
STATUS_INTERRUPTED = "interrupted"
STATUS_FAILED = "failed"
STATUS_COMPLETED = "completed"

# Legacy / in-flight validation
STATUS_VALIDATING = "validating"
EXECUTION_STATUS_VALIDATED = "validated"  # deprecated; use decision-based statuses
EXECUTION_STATUS_FAILED = "failed"

STARTABLE_STATUSES: frozenset[str] = frozenset(
    {STATUS_ALLOWED, STATUS_APPROVED_AFTER_WARNING}
)

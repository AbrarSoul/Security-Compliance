"""Notification types and severity (Sprint 3 Step 6)."""

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"

SEVERITIES: frozenset[str] = frozenset(
    {SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_HIGH, SEVERITY_CRITICAL}
)

SEVERITY_ORDER: dict[str, int] = {
    SEVERITY_INFO: 0,
    SEVERITY_WARNING: 1,
    SEVERITY_HIGH: 2,
    SEVERITY_CRITICAL: 3,
}

# Notification categories
TYPE_PROMPT_BLOCKED = "prompt_blocked"
TYPE_OUTPUT_BLOCKED = "output_blocked"
TYPE_POLICY_VIOLATION = "policy_violation"
TYPE_SUSPICIOUS_ACTIVITY = "suspicious_activity"
TYPE_HIGH_RISK_EXECUTION = "high_risk_execution"
TYPE_REPEATED_VIOLATION = "repeated_violation"
TYPE_SYSTEM_SECURITY = "system_security_alert"

CHANNEL_IN_APP = "in_app"
CHANNEL_EMAIL = "email"
CHANNEL_DASHBOARD = "dashboard"

EMAIL_STATUS_PENDING = "pending"
EMAIL_STATUS_SENT = "sent"
EMAIL_STATUS_SKIPPED = "skipped"
EMAIL_STATUS_FAILED = "failed"

REPEATED_VIOLATION_WINDOW_HOURS = 24
REPEATED_VIOLATION_THRESHOLD = 3

HIGH_RISK_SCORE_MIN = 70

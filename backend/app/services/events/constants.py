"""Canonical monitoring / domain event types (Sprint 3)."""

# Session lifecycle
MONITORING_SESSION_OPENED = "monitoring.session.opened"
MONITORING_SESSION_CLOSED = "monitoring.session.closed"
MONITORING_METRIC_UPDATED = "monitoring.metric.updated"

# Prompt / output
PROMPT_SUBMITTED = "prompt.submitted"
PROMPT_SCANNED = "prompt.scanned"
PROMPT_BLOCKED = "prompt.blocked"
PROMPT_WARNING = "prompt.warning"
OUTPUT_GENERATED = "output.generated"
OUTPUT_SCANNED = "output.scanned"
OUTPUT_BLOCKED = "output.blocked"
OUTPUT_WARNING = "output.warning"

# Compliance guard (Sprint 3 Step 5)
GUARD_ENFORCED = "guard.enforced"
GUARD_PROMPT_BLOCKED = "guard.prompt.blocked"
GUARD_OUTPUT_BLOCKED = "guard.output.blocked"
GUARD_WARNING = "guard.warning"
EXECUTION_INTERRUPTED = "execution.interrupted"

# Compliance & governance
RULE_TRIGGERED = "rule.triggered"
POLICY_VIOLATION = "policy.violation"
EXECUTION_BLOCKED = "execution.blocked"
EXECUTION_STARTED = "execution.started"

# API & security
API_REQUEST = "api.request"
SUSPICIOUS_ACTIVITY = "suspicious.activity.detected"

OUTBOX_PENDING = "pending"
OUTBOX_PROCESSING = "processing"
OUTBOX_PROCESSED = "processed"
OUTBOX_FAILED = "failed"

SESSION_ACTIVE = "active"
SESSION_CLOSED = "closed"

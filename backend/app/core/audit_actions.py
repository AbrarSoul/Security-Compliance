"""Canonical audit action identifiers (dot-separated)."""


class AuditAction:
    # Authentication
    AUTH_SIGNUP = "auth.signup"
    AUTH_LOGIN = "auth.login"
    AUTH_LOGIN_FAILED = "auth.login_failed"
    AUTH_LOGOUT = "auth.logout"
    USER_APPROVED = "user.approved"
    USER_REJECTED = "user.rejected"

    # Files
    FILE_UPLOADED = "file.uploaded"
    FILE_SCANNED = "file.scanned"
    FILE_DELETED = "file.deleted"

    # Compliance / scans
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    COMPLIANCE_RISK_DETECTED = "compliance.risk_detected"
    REPORT_GENERATED = "report.generated"

    # Rules (for future rule management APIs)
    RULE_CREATED = "rule.created"
    RULE_UPDATED = "rule.updated"
    RULE_DISABLED = "rule.disabled"

    # Policies (for future policy management APIs)
    POLICY_CREATED = "policy.created"
    POLICY_UPDATED = "policy.updated"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_DEACTIVATED = "policy.deactivated"
    POLICY_ARCHIVED = "policy.archived"

    # Model compliance
    MODEL_REGISTERED = "model.registered"
    MODEL_UPDATED = "model.updated"
    MODEL_VALIDATED = "model.validated"
    MODEL_VALIDATION_BLOCKED = "model.validation_blocked"

    # Execution (for future execution validation APIs)
    EXECUTION_REQUESTED = "execution.requested"
    EXECUTION_ALLOWED = "execution.allowed"
    EXECUTION_WARNED = "execution.warned"
    EXECUTION_BLOCKED = "execution.blocked"
    EXECUTION_START_REQUESTED = "execution.start_requested"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_WARNING_ACKNOWLEDGED = "execution.warning_acknowledged"
    EXECUTION_START_UNAUTHORIZED = "execution.start_unauthorized"

    # Output compliance (Sprint 3)
    OUTPUT_SCANNED = "output.scanned"
    OUTPUT_ALLOWED = "output.allowed"
    OUTPUT_WARNED = "output.warned"
    OUTPUT_BLOCKED = "output.blocked"

    # Compliance guard (Sprint 3)
    GUARD_ENFORCED = "guard.enforced"
    GUARD_PROMPT_BLOCKED = "guard.prompt.blocked"
    GUARD_OUTPUT_BLOCKED = "guard.output.blocked"
    EXECUTION_INTERRUPTED = "execution.interrupted"

    # Compliance gap analysis (Sprint 3)
    GAP_ANALYSIS_RUN = "gap.analysis_run"
    GAP_DETECTED = "gap.detected"
    GAP_RESOLVED = "gap.resolved"
    GAP_ACKNOWLEDGED = "gap.acknowledged"

    # Security threat detection (Sprint 3)
    THREAT_ANALYSIS_RUN = "threat.analysis_run"
    THREAT_DETECTED = "threat.detected"
    THREAT_INVESTIGATING = "threat.investigating"
    THREAT_RESOLVED = "threat.resolved"

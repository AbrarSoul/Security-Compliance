"""Compliance gap types, categories, and scoring (Sprint 3 Step 8)."""

# Gap types
GAP_MISSING_ENCRYPTION = "missing_encryption"
GAP_MISSING_AUDIT_LOGS = "missing_audit_logs"
GAP_WEAK_RBAC = "weak_rbac"
GAP_INACTIVE_POLICY = "inactive_policy"
GAP_DISABLED_MONITORING = "disabled_monitoring"
GAP_RISKY_MODEL = "risky_model"
GAP_UNAPPROVED_EXTERNAL_API = "unapproved_external_api"
GAP_NO_ENABLED_RULES = "no_enabled_rules"
GAP_UNAPPROVED_MODEL = "unapproved_model"

# Categories
CATEGORY_SECURITY = "security"
CATEGORY_GOVERNANCE = "governance"
CATEGORY_MONITORING = "monitoring"
CATEGORY_ACCESS_CONTROL = "access_control"

# Severity
SEVERITY_CRITICAL = "critical"
SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

SEVERITY_SCORES: dict[str, int] = {
    SEVERITY_CRITICAL: 95,
    SEVERITY_HIGH: 75,
    SEVERITY_MEDIUM: 55,
    SEVERITY_LOW: 35,
}

GAP_STATUS_OPEN = "open"
GAP_STATUS_RESOLVED = "resolved"
GAP_STATUS_ACKNOWLEDGED = "acknowledged"

SCOPE_ORGANIZATION = "organization"
SCOPE_USER = "user"

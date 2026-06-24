"""Canonical permission codes for RBAC (Sprint 2)."""

# User / dataset operations
FILE_UPLOAD = "file:upload"
FILE_READ = "file:read"

SCAN_RUN = "scan:run"
SCAN_READ = "scan:read"

REPORT_READ = "report:read"
REPORT_READ_ALL = "report:read_all"

EXECUTION_REQUEST = "execution:request"
EXECUTION_READ = "execution:read"
EXECUTION_READ_ALL = "execution:read_all"

# Admin
USER_MANAGE = "user:manage"
ROLE_MANAGE = "role:manage"
RULE_MANAGE = "rule:manage"
POLICY_MANAGE = "policy:manage"

# Auditor / compliance visibility
AUDIT_READ = "audit:read"
POLICY_VIOLATION_READ = "policy_violation:read"

# Sprint 3 — real-time monitoring
MONITORING_READ = "monitoring:read"
MONITORING_READ_ALL = "monitoring:read_all"
MONITORING_PUBLISH = "monitoring:publish"
MONITORING_MANAGE = "monitoring:manage"

# Sprint 3 — notifications
NOTIFICATION_READ = "notification:read"
NOTIFICATION_MANAGE = "notification:manage"
NOTIFICATION_READ_ALL = "notification:read_all"

# Sprint 3 — analytics dashboard
ANALYTICS_READ = "analytics:read"
ANALYTICS_READ_ALL = "analytics:read_all"

# Sprint 3 — compliance gap analysis
GAP_READ = "gap:read"
GAP_ANALYZE = "gap:analyze"
GAP_READ_ALL = "gap:read_all"

# Sprint 3 — threat detection
THREAT_READ = "threat:read"
THREAT_READ_ALL = "threat:read_all"
THREAT_MANAGE = "threat:manage"

# GAIRA AI risk assessment
GAIRA_READ = "gaira:read"
GAIRA_MANAGE = "gaira:manage"
GAIRA_READ_ALL = "gaira:read_all"

# Role names (match seeded `roles.name`)
ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_AUDITOR = "auditor"

ALL_PERMISSIONS: tuple[str, ...] = (
    FILE_UPLOAD,
    FILE_READ,
    SCAN_RUN,
    SCAN_READ,
    REPORT_READ,
    REPORT_READ_ALL,
    EXECUTION_REQUEST,
    EXECUTION_READ,
    EXECUTION_READ_ALL,
    USER_MANAGE,
    ROLE_MANAGE,
    RULE_MANAGE,
    POLICY_MANAGE,
    AUDIT_READ,
    POLICY_VIOLATION_READ,
    MONITORING_READ,
    MONITORING_READ_ALL,
    MONITORING_PUBLISH,
    MONITORING_MANAGE,
    NOTIFICATION_READ,
    NOTIFICATION_MANAGE,
    NOTIFICATION_READ_ALL,
    ANALYTICS_READ,
    ANALYTICS_READ_ALL,
    GAP_READ,
    GAP_ANALYZE,
    GAP_READ_ALL,
    THREAT_READ,
    THREAT_READ_ALL,
    THREAT_MANAGE,
    GAIRA_READ,
    GAIRA_MANAGE,
    GAIRA_READ_ALL,
)

ROLE_PERMISSION_MAP: dict[str, tuple[str, ...]] = {
    ROLE_ADMIN: ALL_PERMISSIONS,
    ROLE_USER: (
        FILE_UPLOAD,
        FILE_READ,
        SCAN_RUN,
        SCAN_READ,
        REPORT_READ,
        EXECUTION_REQUEST,
        MONITORING_READ,
        MONITORING_PUBLISH,
        MONITORING_MANAGE,
        NOTIFICATION_READ,
        NOTIFICATION_MANAGE,
        ANALYTICS_READ,
        GAP_READ,
        THREAT_READ,
        GAIRA_READ,
        GAIRA_MANAGE,
    ),
    ROLE_AUDITOR: (
        REPORT_READ_ALL,
        AUDIT_READ,
        POLICY_VIOLATION_READ,
        EXECUTION_READ,
        MONITORING_READ,
        MONITORING_READ_ALL,
        NOTIFICATION_READ,
        NOTIFICATION_READ_ALL,
        ANALYTICS_READ,
        ANALYTICS_READ_ALL,
        GAP_READ,
        GAP_READ_ALL,
        THREAT_READ,
        THREAT_READ_ALL,
        GAIRA_READ,
        GAIRA_READ_ALL,
    ),
}

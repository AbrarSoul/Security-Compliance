"""Gap detection rules (Sprint 3 Step 8)."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.audit_log import AuditLog
from app.models.compliance_model import ComplianceModel
from app.models.compliance_policy import CompliancePolicy
from app.models.compliance_rule import ComplianceRule
from app.models.execution_request import ExecutionRequest
from app.models.user import User
from app.models.user_role import UserRole
from app.repositories.rbac_repository import RbacRepository
from app.services.gaps.constants import (
    CATEGORY_ACCESS_CONTROL,
    CATEGORY_GOVERNANCE,
    CATEGORY_MONITORING,
    CATEGORY_SECURITY,
    GAP_DISABLED_MONITORING,
    GAP_INACTIVE_POLICY,
    GAP_MISSING_AUDIT_LOGS,
    GAP_MISSING_ENCRYPTION,
    GAP_NO_ENABLED_RULES,
    GAP_RISKY_MODEL,
    GAP_UNAPPROVED_EXTERNAL_API,
    GAP_UNAPPROVED_MODEL,
    GAP_WEAK_RBAC,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
    SEVERITY_LOW,
)
from app.services.gaps.types import GapFinding
from app.services.policies.constants import ACTIVE_POLICY_STATUS


class GapRuleContext:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()


async def detect_missing_encryption(ctx: GapRuleContext) -> list[GapFinding]:
    """No at-rest encryption configuration in application settings."""
    findings: list[GapFinding] = []
    if not getattr(ctx.settings, "encryption_at_rest_enabled", False):
        findings.append(
            GapFinding(
                gap_type=GAP_MISSING_ENCRYPTION,
                category=CATEGORY_SECURITY,
                severity=SEVERITY_HIGH,
                title="Encryption at rest not configured",
                description=(
                    "Application settings do not enable encryption at rest for stored "
                    "datasets and uploads."
                ),
                recommendation=(
                    "Enable ENCRYPTION_AT_REST_ENABLED in environment configuration and "
                    "verify storage backend uses encrypted volumes or object storage with "
                    "server-side encryption."
                ),
                metadata={"setting": "encryption_at_rest_enabled", "current": False},
            )
        )
    return findings


async def detect_missing_audit_logs(ctx: GapRuleContext) -> list[GapFinding]:
    """No audit log activity in the recent window."""
    since = datetime.now(UTC) - timedelta(days=7)
    result = await ctx.db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.created_at >= since)
    )
    count = int(result.scalar_one())
    if count == 0:
        return [
            GapFinding(
                gap_type=GAP_MISSING_AUDIT_LOGS,
                category=CATEGORY_GOVERNANCE,
                severity=SEVERITY_CRITICAL,
                title="No recent audit log activity",
                description="No audit log entries were recorded in the last 7 days.",
                recommendation=(
                    "Ensure audit logging is enabled for authentication, file uploads, "
                    "scans, policy changes, and execution events. Review AuditService "
                    "integration across services."
                ),
                metadata={"window_days": 7, "audit_count": 0},
            )
        ]
    return []


async def detect_weak_rbac(ctx: GapRuleContext) -> list[GapFinding]:
    """Users without roles or roles with no permissions."""
    findings: list[GapFinding] = []
    users_result = await ctx.db.execute(select(User.id, User.email).where(User.is_active.is_(True)))
    users = users_result.all()
    rbac = RbacRepository(ctx.db)

    for user_id, email in users:
        roles = await rbac.get_user_role_names(user_id)
        if not roles:
            findings.append(
                GapFinding(
                    gap_type=GAP_WEAK_RBAC,
                    category=CATEGORY_ACCESS_CONTROL,
                    severity=SEVERITY_HIGH,
                    title="User without assigned role",
                    description=f"Active user {email} has no RBAC roles assigned.",
                    recommendation="Assign an appropriate role (user, auditor, or admin) to this account.",
                    resource_type="user",
                    resource_id=user_id,
                    metadata={"email": email},
                )
            )
            continue
        perms = await rbac.get_user_permission_codes(user_id)
        if not perms:
            findings.append(
                GapFinding(
                    gap_type=GAP_WEAK_RBAC,
                    category=CATEGORY_ACCESS_CONTROL,
                    severity=SEVERITY_MEDIUM,
                    title="User role has no permissions",
                    description=f"User {email} has roles {roles} but no effective permissions.",
                    recommendation="Review role-permission mappings in RBAC configuration.",
                    resource_type="user",
                    resource_id=user_id,
                    metadata={"email": email, "roles": roles},
                )
            )

    role_perm_count = await ctx.db.execute(
        select(func.count()).select_from(UserRole)
    )
    if int(role_perm_count.scalar_one()) == 0 and len(users) > 0:
        findings.append(
            GapFinding(
                gap_type=GAP_WEAK_RBAC,
                category=CATEGORY_ACCESS_CONTROL,
                severity=SEVERITY_CRITICAL,
                title="RBAC not configured",
                description="No user-role assignments exist in the system.",
                recommendation="Run RBAC seed migration and assign roles to all active users.",
            )
        )
    return findings


async def detect_inactive_policies(ctx: GapRuleContext) -> list[GapFinding]:
    findings: list[GapFinding] = []
    result = await ctx.db.execute(select(CompliancePolicy))
    policies = result.scalars().all()
    for policy in policies:
        if policy.status != ACTIVE_POLICY_STATUS or not policy.is_active:
            findings.append(
                GapFinding(
                    gap_type=GAP_INACTIVE_POLICY,
                    category=CATEGORY_GOVERNANCE,
                    severity=SEVERITY_MEDIUM if policy.status == "draft" else SEVERITY_HIGH,
                    title=f"Inactive policy: {policy.name}",
                    description=(
                        f"Policy '{policy.name}' has status '{policy.status}' and is not "
                        "actively enforcing compliance."
                    ),
                    recommendation="Activate the policy when ready or archive if obsolete.",
                    resource_type="compliance_policy",
                    resource_id=policy.id,
                    metadata={"status": policy.status, "is_active": policy.is_active},
                )
            )
    if policies and not any(p.status == ACTIVE_POLICY_STATUS for p in policies):
        findings.append(
            GapFinding(
                gap_type=GAP_INACTIVE_POLICY,
                category=CATEGORY_GOVERNANCE,
                severity=SEVERITY_CRITICAL,
                title="No active compliance policies",
                description="No policies are in active status.",
                recommendation="Create and activate at least one compliance policy.",
            )
        )
    return findings


async def detect_disabled_monitoring(ctx: GapRuleContext) -> list[GapFinding]:
    if not ctx.settings.monitoring_outbox_worker_enabled:
        return [
            GapFinding(
                gap_type=GAP_DISABLED_MONITORING,
                category=CATEGORY_MONITORING,
                severity=SEVERITY_HIGH,
                title="Real-time monitoring pipeline disabled",
                description=(
                    "MONITORING_OUTBOX_WORKER_ENABLED is false; domain events are not "
                    "processed for real-time monitoring and notifications."
                ),
                recommendation=(
                    "Set MONITORING_OUTBOX_WORKER_ENABLED=true in production and ensure "
                    "the outbox worker process is running."
                ),
                metadata={"setting": "monitoring_outbox_worker_enabled"},
            )
        ]
    return []


async def detect_no_enabled_rules(ctx: GapRuleContext) -> list[GapFinding]:
    result = await ctx.db.execute(
        select(func.count()).select_from(ComplianceRule).where(ComplianceRule.is_enabled.is_(True))
    )
    if int(result.scalar_one()) == 0:
        return [
            GapFinding(
                gap_type=GAP_NO_ENABLED_RULES,
                category=CATEGORY_GOVERNANCE,
                severity=SEVERITY_HIGH,
                title="No enabled compliance rules",
                description="All compliance rules are disabled or none exist.",
                recommendation="Enable critical rules for PII, secrets, and execution controls.",
            )
        ]
    return []


async def detect_risky_models(ctx: GapRuleContext) -> list[GapFinding]:
    findings: list[GapFinding] = []
    result = await ctx.db.execute(
        select(ComplianceModel).where(ComplianceModel.is_active.is_(True))
    )
    for model in result.scalars().all():
        issues: list[str] = []
        if not model.is_approved:
            issues.append("not approved")
        if model.data_leaves_platform:
            issues.append("data leaves platform")
        if model.logging_enabled is False:
            issues.append("logging disabled")
        if model.model_type in ("external_api", "cloud_hosted") and not model.is_approved:
            issues.append("external/cloud without approval")

        if not issues:
            continue

        severity = SEVERITY_CRITICAL if "not approved" in issues and model.data_leaves_platform else SEVERITY_HIGH
        findings.append(
            GapFinding(
                gap_type=GAP_RISKY_MODEL,
                category=CATEGORY_SECURITY,
                severity=severity,
                title=f"Risky model configuration: {model.name}",
                description=f"Model '{model.name}' ({model.code}): {', '.join(issues)}.",
                recommendation=(
                    "Approve the model after review, enable logging, and restrict data "
                    "leaving the platform unless required."
                ),
                resource_type="compliance_model",
                resource_id=model.id,
                metadata={"code": model.code, "issues": issues},
            )
        )
    return findings


async def detect_unapproved_external_apis(ctx: GapRuleContext) -> list[GapFinding]:
    findings: list[GapFinding] = []
    models_result = await ctx.db.execute(
        select(ComplianceModel).where(
            ComplianceModel.is_active.is_(True),
            ComplianceModel.is_approved.is_(False),
            ComplianceModel.model_type.in_(("external_api", "cloud_hosted")),
        )
    )
    for model in models_result.scalars().all():
        findings.append(
            GapFinding(
                gap_type=GAP_UNAPPROVED_EXTERNAL_API,
                category=CATEGORY_SECURITY,
                severity=SEVERITY_CRITICAL,
                title=f"Unapproved external API: {model.name}",
                description=(
                    f"Model '{model.name}' is type '{model.model_type}' and is not approved "
                    "for production use."
                ),
                recommendation=(
                    "Complete model compliance validation and set is_approved=true "
                    "before allowing executions."
                ),
                resource_type="compliance_model",
                resource_id=model.id,
                metadata={"model_type": model.model_type, "endpoint": model.endpoint_url},
            )
        )

    exec_result = await ctx.db.execute(
        select(ExecutionRequest).where(
            ExecutionRequest.is_external_api.is_(True),
            ExecutionRequest.status.notin_(("blocked", "failed")),
        )
    )
    for ex in exec_result.scalars().all():
        if ex.compliance_model_id:
            model = await ctx.db.get(ComplianceModel, ex.compliance_model_id)
            if model and not model.is_approved:
                findings.append(
                    GapFinding(
                        gap_type=GAP_UNAPPROVED_EXTERNAL_API,
                        category=CATEGORY_SECURITY,
                        severity=SEVERITY_CRITICAL,
                        title="Execution using unapproved external API",
                        description=(
                            f"Execution {ex.id} uses an unapproved external API model."
                        ),
                        recommendation="Block execution until model is approved.",
                        resource_type="execution_request",
                        resource_id=ex.id,
                        metadata={"model_id": str(ex.compliance_model_id)},
                    )
                )
    return findings


async def detect_unapproved_models(ctx: GapRuleContext) -> list[GapFinding]:
    result = await ctx.db.execute(
        select(ComplianceModel).where(
            ComplianceModel.is_active.is_(True),
            ComplianceModel.is_approved.is_(False),
            ComplianceModel.model_type.notin_(("external_api", "cloud_hosted")),
        )
    )
    return [
        GapFinding(
            gap_type=GAP_UNAPPROVED_MODEL,
            category=CATEGORY_GOVERNANCE,
            severity=SEVERITY_MEDIUM,
            title=f"Unapproved model: {m.name}",
            description=f"Active model '{m.name}' has not been approved.",
            recommendation="Run model compliance validation and approve when passing.",
            resource_type="compliance_model",
            resource_id=m.id,
            metadata={"code": m.code},
        )
        for m in result.scalars().all()
    ]


ALL_GAP_DETECTORS = [
    detect_missing_encryption,
    detect_missing_audit_logs,
    detect_weak_rbac,
    detect_inactive_policies,
    detect_disabled_monitoring,
    detect_no_enabled_rules,
    detect_risky_models,
    detect_unapproved_external_apis,
    detect_unapproved_models,
]

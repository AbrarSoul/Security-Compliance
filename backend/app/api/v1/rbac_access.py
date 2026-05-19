"""Example routes demonstrating Admin / User / Auditor RBAC (Sprint 2 Step 2)."""

from fastapi import APIRouter, Depends

from app.auth.rbac import AuthContext, require_permission, require_role
from app.auth.schemas import MessageResponse
from app.core.permissions import (
    AUDIT_READ,
    EXECUTION_REQUEST,
    POLICY_MANAGE,
    POLICY_VIOLATION_READ,
    ROLE_ADMIN,
    ROLE_AUDITOR,
    ROLE_USER,
    USER_MANAGE,
)

router = APIRouter(prefix="/rbac", tags=["rbac-examples"])


@router.get("/admin/system", response_model=MessageResponse)
async def admin_only_system(ctx: AuthContext = Depends(require_role(ROLE_ADMIN))):
    """Admin-only: full platform administration surface."""
    return MessageResponse(
        message=f"Admin access granted for {ctx.user.email}",
    )


@router.get("/admin/users", response_model=MessageResponse)
async def admin_manage_users(ctx: AuthContext = Depends(require_permission(USER_MANAGE))):
    """Admin-only via permission: manage users."""
    return MessageResponse(message="User management endpoint (admin permission)")


@router.post("/user/execution-validation", response_model=MessageResponse)
async def user_request_execution(
    ctx: AuthContext = Depends(require_permission(EXECUTION_REQUEST)),
):
    """Standard user: request pre-execution compliance validation."""
    return MessageResponse(
        message=f"Execution validation may be requested by {ctx.user.email}",
    )


@router.get("/user/files-summary", response_model=MessageResponse)
async def user_files_summary(ctx: AuthContext = Depends(require_role(ROLE_USER))):
    """User role example: dataset operations."""
    return MessageResponse(message="User file operations scope")


@router.get("/auditor/reports", response_model=MessageResponse)
async def auditor_view_reports(ctx: AuthContext = Depends(require_role(ROLE_AUDITOR))):
    """Auditor-only: read-only reports access."""
    return MessageResponse(message="Auditor reports read scope (all reports)")


@router.get("/auditor/audit-logs", response_model=MessageResponse)
async def auditor_audit_logs(ctx: AuthContext = Depends(require_permission(AUDIT_READ))):
    """Auditor: use GET /api/v1/audit-logs for paginated audit history."""
    return MessageResponse(
        message="Auditor audit access granted. Use GET /api/v1/audit-logs.",
    )


@router.get("/auditor/policy-violations", response_model=MessageResponse)
async def auditor_policy_violations(
    ctx: AuthContext = Depends(require_permission(POLICY_VIOLATION_READ)),
):
    """Auditor: view policy violations without modify access."""
    return MessageResponse(message="Auditor policy violations read scope")


@router.post("/auditor/cannot-manage-policies", response_model=MessageResponse)
async def auditor_blocked_from_policies(
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
):
    """Intentionally requires policy:manage — auditors receive 403."""
    return MessageResponse(message="Should not be reachable by auditors")

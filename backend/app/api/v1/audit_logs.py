"""Read-only audit log API (Admin and Auditor)."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import AUDIT_READ
from app.db.session import get_db
from app.repositories.audit_repository import AuditLogFilters, AuditRepository
from app.schemas.audit import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def get_audit_repo(db: AsyncSession = Depends(get_db)) -> AuditRepository:
    return AuditRepository(db)


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    _ctx: AuthContext = Depends(require_permission(AUDIT_READ)),
    user_id: UUID | None = Query(default=None, description="Filter by actor user id"),
    action: str | None = Query(default=None, description="Exact action match"),
    action_prefix: str | None = Query(
        default=None, description="Action prefix, e.g. auth. or file."
    ),
    severity: str | None = Query(default=None),
    status: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repo: AuditRepository = Depends(get_audit_repo),
):
    """
    List audit logs (append-only; no update/delete endpoints).

    Requires `audit:read` (Admin and Auditor).
    """
    filters = AuditLogFilters(
        user_id=user_id,
        action=action,
        action_prefix=action_prefix,
        severity=severity,
        status=status,
        resource_type=resource_type,
        created_from=created_from,
        created_to=created_to,
    )
    items = await repo.list_filtered(filters, limit=limit, offset=offset)
    total = await repo.count_filtered(filters)
    return AuditLogListResponse(
        items=[AuditLogResponse.from_model(row) for row in items],
        total=total,
        limit=limit,
        offset=offset,
    )

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import USER_MANAGE
from app.db.session import get_db
from app.schemas.users import (
    ApproveUserRequest,
    PendingUserListResponse,
    PendingUserResponse,
    UserActionResponse,
)
from app.services.user_management_service import UserManagementService

router = APIRouter(prefix="/users", tags=["user-management"])


def get_user_management_service(db: AsyncSession = Depends(get_db)) -> UserManagementService:
    return UserManagementService(db)


@router.get("/pending", response_model=PendingUserListResponse)
async def list_pending_registrations(
    ctx: AuthContext = Depends(require_permission(USER_MANAGE)),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: UserManagementService = Depends(get_user_management_service),
):
    """List accounts awaiting admin approval."""
    items, total = await service.list_pending(limit=limit, offset=offset)
    return PendingUserListResponse(
        items=[PendingUserResponse.model_validate(u) for u in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{user_id}/approve",
    response_model=UserActionResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_registration(
    user_id: UUID,
    body: ApproveUserRequest,
    ctx: AuthContext = Depends(require_permission(USER_MANAGE)),
    service: UserManagementService = Depends(get_user_management_service),
):
    """Approve a pending registration and assign a role."""
    await service.approve(user_id, body.role, actor_user_id=ctx.user.id)
    return UserActionResponse(
        message=f"User approved with role '{body.role}'",
        user_id=user_id,
    )


@router.post(
    "/{user_id}/reject",
    response_model=UserActionResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_registration(
    user_id: UUID,
    ctx: AuthContext = Depends(require_permission(USER_MANAGE)),
    service: UserManagementService = Depends(get_user_management_service),
):
    """Reject a pending registration."""
    await service.reject(user_id, actor_user_id=ctx.user.id)
    return UserActionResponse(message="Registration rejected", user_id=user_id)

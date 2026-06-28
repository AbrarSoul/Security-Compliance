from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.core.permissions import ROLE_ADMIN, ROLE_AUDITOR, ROLE_USER
from app.core.user_approval import (
    APPROVAL_APPROVED,
    APPROVAL_PENDING,
    APPROVAL_REJECTED,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_service import AuditService
from app.services.rbac_service import RbacService

ASSIGNABLE_ROLES = frozenset({ROLE_ADMIN, ROLE_USER, ROLE_AUDITOR})


class UserManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.users = UserRepository(db)
        self.rbac = RbacService(db)
        self.audit = AuditService(db)

    async def list_pending(self, *, limit: int = 100, offset: int = 0):
        return await self.users.list_by_approval_status(
            APPROVAL_PENDING, limit=limit, offset=offset
        )

    async def approve(self, user_id: UUID, role_name: str, *, actor_user_id: UUID) -> None:
        if role_name not in ASSIGNABLE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role must be one of: {', '.join(sorted(ASSIGNABLE_ROLES))}",
            )

        user = await self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.approval_status != APPROVAL_PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending registrations can be approved",
            )

        user.approval_status = APPROVAL_APPROVED
        user.is_active = True
        await self.rbac.set_user_role(user.id, role_name)
        await self.audit.log(
            AuditAction.USER_APPROVED,
            user_id=actor_user_id,
            resource_type="user",
            resource_id=user.id,
            severity=audit_severity.INFO,
            status="success",
            metadata={"email": user.email, "role": role_name},
        )

    async def reject(self, user_id: UUID, *, actor_user_id: UUID) -> None:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if user.approval_status != APPROVAL_PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending registrations can be rejected",
            )

        user.approval_status = APPROVAL_REJECTED
        user.is_active = False
        await self.audit.log(
            AuditAction.USER_REJECTED,
            user_id=actor_user_id,
            resource_type="user",
            resource_id=user.id,
            severity=audit_severity.MEDIUM,
            status="success",
            metadata={"email": user.email},
        )

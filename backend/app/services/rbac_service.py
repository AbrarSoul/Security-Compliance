from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ROLE_USER
from app.repositories.rbac_repository import RbacRepository


@dataclass(frozen=True)
class UserRbac:
    roles: list[str]
    permissions: list[str]


class RbacService:
    def __init__(self, db: AsyncSession):
        self.repo = RbacRepository(db)

    async def get_user_rbac(self, user_id: UUID) -> UserRbac:
        roles = await self.repo.get_user_role_names(user_id)
        permissions = await self.repo.get_user_permission_codes(user_id)
        return UserRbac(roles=roles, permissions=permissions)

    async def assign_default_role(self, user_id: UUID) -> None:
        """Assign the standard User role to a newly registered account."""
        await self.repo.assign_role_by_name(user_id, ROLE_USER)

    async def assign_role(self, user_id: UUID, role_name: str) -> None:
        assigned = await self.repo.assign_role_by_name(user_id, role_name)
        if assigned is None:
            raise ValueError(f"Role not found: {role_name}")

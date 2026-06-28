from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.user_approval import APPROVAL_PENDING
from app.models.user import User
from app.models.user_role import UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        password_hash: str,
        full_name: str | None = None,
        *,
        is_active: bool = True,
        approval_status: str | None = None,
    ) -> User:
        user = User(
            email=email.lower(),
            password_hash=password_hash,
            full_name=full_name,
            is_active=is_active,
            approval_status=approval_status or ("approved" if is_active else APPROVAL_PENDING),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def email_exists(self, email: str) -> bool:
        user = await self.get_by_email(email)
        return user is not None

    async def list_by_approval_status(
        self,
        approval_status: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        query = (
            select(User)
            .options(selectinload(User.user_roles))
            .where(User.approval_status == approval_status)
            .order_by(User.created_at.desc())
        )
        count_result = await self.db.execute(
            select(func.count()).select_from(User).where(User.approval_status == approval_status)
        )
        total = int(count_result.scalar_one())
        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().unique().all()), total

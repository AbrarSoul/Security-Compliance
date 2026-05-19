"""Persistence for notifications and preferences."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.models.user_role import UserRole
from app.models.role import Role


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: UUID,
        *,
        unread_only: bool = False,
        notification_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            base = base.where(Notification.is_read.is_(False))
        if notification_type:
            base = base.where(Notification.notification_type == notification_type)
        if severity:
            base = base.where(Notification.severity == severity)

        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_q)).scalar_one())

        result = await self.db.execute(
            base.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def count_unread(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
        )
        return int(result.scalar_one())

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> Notification | None:
        notification = await self.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id:
            return None
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self.db.flush()
        return notification

    async def mark_all_read(self, user_id: UUID) -> int:
        now = datetime.now(UTC)
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=now)
        )
        return result.rowcount or 0

    async def count_recent_by_type(
        self,
        user_id: UUID,
        notification_type: str,
        *,
        window_hours: int,
    ) -> int:
        since = datetime.now(UTC) - timedelta(hours=window_hours)
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.notification_type == notification_type,
                Notification.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def get_preferences(self, user_id: UUID) -> NotificationPreference | None:
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_preferences(self, user_id: UUID) -> NotificationPreference:
        prefs = await self.get_preferences(user_id)
        if prefs is not None:
            return prefs
        prefs = NotificationPreference(user_id=user_id)
        self.db.add(prefs)
        await self.db.flush()
        return prefs

    async def update_preferences(
        self, prefs: NotificationPreference, **fields: object
    ) -> NotificationPreference:
        for key, value in fields.items():
            if value is not None and hasattr(prefs, key):
                setattr(prefs, key, value)
        await self.db.flush()
        return prefs

    async def get_user_email(self, user_id: UUID) -> str | None:
        result = await self.db.execute(select(User.email).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_user_ids_by_role(self, role_name: str) -> list[UUID]:
        result = await self.db.execute(
            select(UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .where(Role.name == role_name)
        )
        return list(result.scalars().all())

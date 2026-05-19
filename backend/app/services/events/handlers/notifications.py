"""Creates user notifications from processed domain events."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.events.handlers.base import EventHandler
from app.services.notifications.notification_service import NotificationService


class NotificationEventHandler(EventHandler):
    async def handle(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        service = NotificationService(db)
        await service.process_domain_event(payload)

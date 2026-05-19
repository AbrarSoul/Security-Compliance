from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.events.handlers.base import EventHandler
from app.services.events.constants import (
    EXECUTION_BLOCKED,
    EXECUTION_INTERRUPTED,
    GUARD_OUTPUT_BLOCKED,
    GUARD_PROMPT_BLOCKED,
    OUTPUT_BLOCKED,
    POLICY_VIOLATION,
    PROMPT_BLOCKED,
    RULE_TRIGGERED,
    SUSPICIOUS_ACTIVITY,
)
from app.services.events.handlers.monitoring_status import MonitoringStatusHandler
from app.services.events.handlers.notifications import NotificationEventHandler
from app.services.events.handlers.threat_detection import ThreatDetectionEventHandler


class EventHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def register(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def register_global(self, handler: EventHandler) -> None:
        self._handlers.setdefault("*", []).append(handler)

    async def dispatch(
        self, db: AsyncSession, event_type: str, payload: dict[str, Any]
    ) -> None:
        handlers = list(self._handlers.get(event_type, []))
        handlers.extend(self._handlers.get("*", []))
        for handler in handlers:
            await handler.handle(db, payload)


_NOTIFY_TYPES = (
    PROMPT_BLOCKED,
    OUTPUT_BLOCKED,
    POLICY_VIOLATION,
    SUSPICIOUS_ACTIVITY,
    EXECUTION_BLOCKED,
    EXECUTION_INTERRUPTED,
    GUARD_PROMPT_BLOCKED,
    GUARD_OUTPUT_BLOCKED,
    RULE_TRIGGERED,
)


def build_default_registry() -> EventHandlerRegistry:
    registry = EventHandlerRegistry()
    status_handler = MonitoringStatusHandler()
    registry.register_global(status_handler)
    notification_handler = NotificationEventHandler()
    for event_type in _NOTIFY_TYPES:
        registry.register(event_type, notification_handler)
    threat_handler = ThreatDetectionEventHandler()
    for event_type in _NOTIFY_TYPES:
        registry.register(event_type, threat_handler)
    return registry

"""Real-time threat detection from domain events."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.events.constants import (
    EXECUTION_BLOCKED,
    EXECUTION_INTERRUPTED,
    GUARD_PROMPT_BLOCKED,
    OUTPUT_BLOCKED,
    POLICY_VIOLATION,
    PROMPT_BLOCKED,
    RULE_TRIGGERED,
)
from app.services.events.handlers.base import EventHandler
from app.services.threats.security_monitoring_service import SecurityMonitoringService

_THREAT_EVENT_TYPES = frozenset(
    {
        PROMPT_BLOCKED,
        OUTPUT_BLOCKED,
        POLICY_VIOLATION,
        EXECUTION_BLOCKED,
        EXECUTION_INTERRUPTED,
        GUARD_PROMPT_BLOCKED,
        RULE_TRIGGERED,
    }
)


class ThreatDetectionEventHandler(EventHandler):
    async def handle(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        event_type = str(payload.get("event_type", ""))
        if event_type not in _THREAT_EVENT_TYPES:
            return
        service = SecurityMonitoringService(db)
        await service.process_domain_event(payload)

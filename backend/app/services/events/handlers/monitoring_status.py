"""Updates monitoring session counters from processed domain events."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.monitoring_repository import MonitoringRepository
from app.services.events.constants import (
    EXECUTION_BLOCKED,
    POLICY_VIOLATION,
    EXECUTION_INTERRUPTED,
    GUARD_OUTPUT_BLOCKED,
    GUARD_PROMPT_BLOCKED,
    OUTPUT_BLOCKED,
    PROMPT_BLOCKED,
    RULE_TRIGGERED,
    SUSPICIOUS_ACTIVITY,
)
from app.services.events.handlers.base import EventHandler

_ALERT_EVENT_TYPES = frozenset(
    {
        RULE_TRIGGERED,
        POLICY_VIOLATION,
        EXECUTION_BLOCKED,
        SUSPICIOUS_ACTIVITY,
        PROMPT_BLOCKED,
        OUTPUT_BLOCKED,
        GUARD_PROMPT_BLOCKED,
        GUARD_OUTPUT_BLOCKED,
        EXECUTION_INTERRUPTED,
    }
)


class MonitoringStatusHandler(EventHandler):
    async def handle(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        session_id_raw = payload.get("session_id")
        if not session_id_raw:
            return

        session_id = UUID(str(session_id_raw))
        repo = MonitoringRepository(db)
        session = await repo.get_session(session_id)
        if session is None or session.status != "active":
            return

        event_type = str(payload.get("event_type", ""))
        session.event_count += 1
        session.last_event_type = event_type

        if event_type in _ALERT_EVENT_TYPES:
            session.alert_count += 1

        risk = payload.get("payload", {}).get("risk_score")
        if risk is not None:
            try:
                session.last_risk_score = int(risk)
            except (TypeError, ValueError):
                pass

        await repo.update_session(session)

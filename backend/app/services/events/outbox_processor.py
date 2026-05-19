"""Async worker that drains the transactional outbox and dispatches handlers."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories.monitoring_repository import MonitoringRepository
from app.services.events.handlers.registry import EventHandlerRegistry, build_default_registry
from app.services.events.pubsub import monitoring_pubsub

logger = logging.getLogger(__name__)


class OutboxProcessor:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        registry: EventHandlerRegistry | None = None,
        batch_size: int = 25,
    ):
        self._session_factory = session_factory
        self._registry = registry or build_default_registry()
        self._batch_size = batch_size

    async def process_batch(self) -> int:
        processed = 0
        async with self._session_factory() as db:
            repo = MonitoringRepository(db)
            rows = await repo.claim_pending_outbox(batch_size=self._batch_size)
            if not rows:
                return 0

            for row in rows:
                try:
                    await self._registry.dispatch(db, row.event_type, row.payload_json)
                    await repo.mark_outbox_processed(row)
                    await self._broadcast(row.payload_json)
                    processed += 1
                except Exception as exc:
                    logger.exception("Outbox handler failed for %s", row.id)
                    await repo.mark_outbox_failed(row, str(exc))

            await db.commit()
        return processed

    async def _broadcast(self, payload: dict[str, Any]) -> None:
        session_raw = payload.get("session_id")
        session_id = UUID(str(session_raw)) if session_raw else None
        await monitoring_pubsub.publish(payload, session_id=session_id)

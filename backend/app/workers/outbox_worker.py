"""Background loop that polls the transactional outbox."""

import asyncio
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.event_outbox import EventOutbox
from app.services.events.outbox_processor import OutboxProcessor

logger = logging.getLogger(__name__)


class OutboxWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        poll_interval_seconds: float = 1.0,
        batch_size: int = 25,
    ):
        self._session_factory = session_factory
        self._poll_interval = poll_interval_seconds
        self._processor = OutboxProcessor(session_factory, batch_size=batch_size)
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name="outbox-worker")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _run(self) -> None:
        logger.info("Outbox worker started (interval=%ss)", self._poll_interval)
        while not self._stop.is_set():
            try:
                processed = await self._processor.process_batch()
                if processed:
                    logger.debug("Processed %s outbox rows", processed)
            except Exception:
                logger.exception("Outbox worker batch failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._poll_interval)
            except asyncio.TimeoutError:
                continue
        logger.info("Outbox worker stopped")

    async def pending_count(self) -> int:
        async with self._session_factory() as db:
            result = await db.execute(
                select(func.count())
                .select_from(EventOutbox)
                .where(EventOutbox.status == "pending")
            )
            return int(result.scalar_one())

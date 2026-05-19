"""Shared outbox worker instance for app lifespan and monitoring status API."""

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.workers.outbox_worker import OutboxWorker

_settings = get_settings()
outbox_worker = OutboxWorker(
    AsyncSessionLocal,
    poll_interval_seconds=_settings.monitoring_outbox_poll_seconds,
    batch_size=_settings.monitoring_outbox_batch_size,
)

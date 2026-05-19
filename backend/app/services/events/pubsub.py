"""In-process pub/sub for real-time monitoring subscribers (SSE / WebSocket)."""

import asyncio
from collections import defaultdict
from typing import Any
from uuid import UUID


class MonitoringEventPubSub:
    """Thread-safe async pub/sub keyed by monitoring session id."""

    def __init__(self) -> None:
        self._queues: dict[UUID, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._global_queues: list[asyncio.Queue[dict[str, Any]]] = []
        self._lock = asyncio.Lock()

    async def subscribe(self, session_id: UUID | None = None) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        async with self._lock:
            if session_id is None:
                self._global_queues.append(queue)
            else:
                self._queues[session_id].append(queue)
        return queue

    async def unsubscribe(
        self, queue: asyncio.Queue[dict[str, Any]], session_id: UUID | None = None
    ) -> None:
        async with self._lock:
            if session_id is None:
                if queue in self._global_queues:
                    self._global_queues.remove(queue)
            else:
                subs = self._queues.get(session_id, [])
                if queue in subs:
                    subs.remove(queue)

    async def publish(self, message: dict[str, Any], session_id: UUID | None = None) -> None:
        async with self._lock:
            targets: list[asyncio.Queue[dict[str, Any]]] = list(self._global_queues)
            if session_id is not None:
                targets.extend(self._queues.get(session_id, []))
        for queue in targets:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(message)


# Singleton used by API stream and outbox processor
monitoring_pubsub = MonitoringEventPubSub()

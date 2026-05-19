"""In-process pub/sub for real-time dashboard notification alerts (SSE)."""

import asyncio
from collections import defaultdict
from typing import Any
from uuid import UUID


class NotificationPubSub:
    """Async pub/sub keyed by user id for dashboard alert streams."""

    def __init__(self) -> None:
        self._queues: dict[UUID, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._admin_queues: list[asyncio.Queue[dict[str, Any]]] = []
        self._lock = asyncio.Lock()

    async def subscribe(
        self, user_id: UUID | None = None, *, admin_stream: bool = False
    ) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=256)
        async with self._lock:
            if admin_stream:
                self._admin_queues.append(queue)
            elif user_id is not None:
                self._queues[user_id].append(queue)
        return queue

    async def unsubscribe(
        self,
        queue: asyncio.Queue[dict[str, Any]],
        user_id: UUID | None = None,
        *,
        admin_stream: bool = False,
    ) -> None:
        async with self._lock:
            if admin_stream:
                if queue in self._admin_queues:
                    self._admin_queues.remove(queue)
            elif user_id is not None:
                subs = self._queues.get(user_id, [])
                if queue in subs:
                    subs.remove(queue)

    async def publish(self, user_id: UUID, message: dict[str, Any]) -> None:
        async with self._lock:
            targets: list[asyncio.Queue[dict[str, Any]]] = list(self._queues.get(user_id, []))
            targets.extend(self._admin_queues)
        for queue in targets:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(message)


notification_pubsub = NotificationPubSub()

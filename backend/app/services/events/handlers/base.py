from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class EventHandler(ABC):
    @abstractmethod
    async def handle(self, db: AsyncSession, payload: dict[str, Any]) -> None:
        """Process a single outbox payload."""

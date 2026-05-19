from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent
from app.models.event_outbox import EventOutbox
from app.models.monitoring_session import MonitoringSession


class MonitoringRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session: MonitoringSession) -> MonitoringSession:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: UUID) -> MonitoringSession | None:
        result = await self.db.execute(
            select(MonitoringSession).where(MonitoringSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_for_user(
        self, session_id: UUID, user_id: UUID
    ) -> MonitoringSession | None:
        result = await self.db.execute(
            select(MonitoringSession).where(
                MonitoringSession.id == session_id,
                MonitoringSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_session_for_execution(
        self, execution_request_id: UUID
    ) -> MonitoringSession | None:
        result = await self.db.execute(
            select(MonitoringSession).where(
                MonitoringSession.execution_request_id == execution_request_id,
                MonitoringSession.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        *,
        user_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MonitoringSession]:
        query: Select = select(MonitoringSession).order_by(MonitoringSession.opened_at.desc())
        if user_id is not None:
            query = query.where(MonitoringSession.user_id == user_id)
        if status is not None:
            query = query.where(MonitoringSession.status == status)
        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_sessions(
        self, *, user_id: UUID | None = None, status: str | None = None
    ) -> int:
        query = select(func.count()).select_from(MonitoringSession)
        if user_id is not None:
            query = query.where(MonitoringSession.user_id == user_id)
        if status is not None:
            query = query.where(MonitoringSession.status == status)
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def update_session(self, session: MonitoringSession) -> MonitoringSession:
        await self.db.flush()
        return session

    async def create_domain_event(self, event: DomainEvent) -> DomainEvent:
        self.db.add(event)
        await self.db.flush()
        return event

    async def create_outbox_row(self, row: EventOutbox) -> EventOutbox:
        self.db.add(row)
        await self.db.flush()
        return row

    async def list_domain_events(
        self,
        *,
        session_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DomainEvent]:
        query = select(DomainEvent).order_by(DomainEvent.occurred_at.desc())
        if session_id is not None:
            query = query.where(DomainEvent.session_id == session_id)
        if event_type is not None:
            query = query.where(DomainEvent.event_type == event_type)
        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_domain_events(
        self, *, session_id: UUID | None = None, event_type: str | None = None
    ) -> int:
        query = select(func.count()).select_from(DomainEvent)
        if session_id is not None:
            query = query.where(DomainEvent.session_id == session_id)
        if event_type is not None:
            query = query.where(DomainEvent.event_type == event_type)
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def claim_pending_outbox(self, *, batch_size: int = 25) -> list[EventOutbox]:
        result = await self.db.execute(
            select(EventOutbox)
            .where(EventOutbox.status == "pending")
            .order_by(EventOutbox.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        rows = list(result.scalars().all())
        for row in rows:
            row.status = "processing"
            row.attempts += 1
        if rows:
            await self.db.flush()
        return rows

    async def mark_outbox_processed(self, row: EventOutbox) -> None:
        from datetime import UTC, datetime

        row.status = "processed"
        row.processed_at = datetime.now(UTC)
        row.last_error = None
        await self.db.flush()

    async def mark_outbox_failed(self, row: EventOutbox, error: str) -> None:
        row.status = "failed"
        row.last_error = error[:4000]
        await self.db.flush()

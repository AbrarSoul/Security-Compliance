"""Persists domain events and enqueues outbox rows in the same DB transaction."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent
from app.models.event_outbox import EventOutbox
from app.repositories.monitoring_repository import MonitoringRepository
from app.services.events.constants import OUTBOX_PENDING
from app.services.events.types import DomainEventEnvelope


class EventDispatcher:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MonitoringRepository(db)

    async def publish(self, envelope: DomainEventEnvelope) -> DomainEvent:
        event = DomainEvent(
            id=envelope.event_id,
            event_type=envelope.event_type,
            user_id=envelope.user_id,
            session_id=envelope.session_id,
            correlation_id=envelope.correlation_id,
            resource_type=envelope.resource_type,
            resource_id=envelope.resource_id,
            severity=envelope.severity,
            source=envelope.source,
            payload_json=envelope.payload,
            occurred_at=envelope.occurred_at,
        )
        await self.repo.create_domain_event(event)

        outbox_payload = envelope.to_dict()
        outbox = EventOutbox(
            domain_event_id=event.id,
            event_type=envelope.event_type,
            payload_json=outbox_payload,
            status=OUTBOX_PENDING,
        )
        await self.repo.create_outbox_row(outbox)
        return event

    async def publish_many(self, envelopes: list[DomainEventEnvelope]) -> list[DomainEvent]:
        events: list[DomainEvent] = []
        for envelope in envelopes:
            events.append(await self.publish(envelope))
        return events

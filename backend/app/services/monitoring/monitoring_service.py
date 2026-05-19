"""High-level monitoring API: sessions, event ingest, status."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent
from app.models.monitoring_session import MonitoringSession
from app.repositories.monitoring_repository import MonitoringRepository
from app.services.events.constants import (
    EXECUTION_BLOCKED,
    EXECUTION_STARTED,
    MONITORING_SESSION_CLOSED,
    MONITORING_SESSION_OPENED,
    OUTPUT_GENERATED,
    PROMPT_SUBMITTED,
    RULE_TRIGGERED,
    SESSION_ACTIVE,
    SESSION_CLOSED,
    SUSPICIOUS_ACTIVITY,
)
from app.services.events.dispatcher import EventDispatcher
from app.services.events.types import DomainEventEnvelope


class MonitoringService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MonitoringRepository(db)
        self.dispatcher = EventDispatcher(db)

    async def open_session(
        self,
        *,
        user_id: UUID,
        execution_request_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> MonitoringSession:
        if execution_request_id is not None:
            existing = await self.repo.get_active_session_for_execution(execution_request_id)
            if existing is not None:
                return existing

        session = MonitoringSession(
            user_id=user_id,
            execution_request_id=execution_request_id,
            status=SESSION_ACTIVE,
            metadata_json=metadata,
        )
        await self.repo.create_session(session)

        await self.dispatcher.publish(
            DomainEventEnvelope(
                event_type=MONITORING_SESSION_OPENED,
                user_id=user_id,
                session_id=session.id,
                resource_type="monitoring_session",
                resource_id=session.id,
                payload={
                    "execution_request_id": str(execution_request_id)
                    if execution_request_id
                    else None,
                },
            )
        )
        return session

    async def close_session(
        self,
        session_id: UUID,
        *,
        user_id: UUID,
        can_manage_all: bool = False,
    ) -> MonitoringSession:
        session = await self._get_session_for_access(
            session_id, user_id=user_id, can_read_all=can_manage_all
        )
        if session.status == SESSION_CLOSED:
            return session

        session.status = SESSION_CLOSED
        session.closed_at = datetime.now(UTC)
        await self.repo.update_session(session)
        await self.db.refresh(session)

        await self.dispatcher.publish(
            DomainEventEnvelope(
                event_type=MONITORING_SESSION_CLOSED,
                user_id=user_id,
                session_id=session.id,
                resource_type="monitoring_session",
                resource_id=session.id,
            )
        )
        return session

    async def publish_event(
        self,
        *,
        event_type: str,
        user_id: UUID,
        session_id: UUID | None = None,
        payload: dict | None = None,
        severity: str = "info",
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        correlation_id: UUID | None = None,
        source: str = "api",
    ) -> DomainEvent:
        if session_id is not None:
            session = await self.repo.get_session(session_id)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Monitoring session not found",
                )
            if session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not allowed to publish to this session",
                )

        envelope = DomainEventEnvelope(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            payload=payload or {},
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            correlation_id=correlation_id,
            source=source,
        )
        return await self.dispatcher.publish(envelope)

    async def record_prompt_submitted(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        prompt_ref: str,
        metadata: dict | None = None,
    ) -> DomainEvent:
        return await self.publish_event(
            event_type=PROMPT_SUBMITTED,
            user_id=user_id,
            session_id=session_id,
            payload={"prompt_ref": prompt_ref, **(metadata or {})},
            resource_type="prompt",
        )

    async def record_output_generated(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        output_ref: str,
        metadata: dict | None = None,
    ) -> DomainEvent:
        return await self.publish_event(
            event_type=OUTPUT_GENERATED,
            user_id=user_id,
            session_id=session_id,
            payload={"output_ref": output_ref, **(metadata or {})},
            resource_type="output",
        )

    async def record_rule_triggered(
        self,
        *,
        user_id: UUID,
        session_id: UUID | None,
        rule_id: UUID,
        rule_code: str,
        metadata: dict | None = None,
    ) -> DomainEvent:
        return await self.publish_event(
            event_type=RULE_TRIGGERED,
            user_id=user_id,
            session_id=session_id,
            severity="warning",
            resource_type="compliance_rule",
            resource_id=rule_id,
            payload={"rule_code": rule_code, **(metadata or {})},
        )

    async def record_execution_blocked(
        self,
        *,
        user_id: UUID,
        execution_request_id: UUID,
        reason: str,
        session_id: UUID | None = None,
    ) -> DomainEvent:
        if session_id is None:
            session = await self.repo.get_active_session_for_execution(execution_request_id)
            session_id = session.id if session else None

        return await self.publish_event(
            event_type=EXECUTION_BLOCKED,
            user_id=user_id,
            session_id=session_id,
            severity="high",
            resource_type="execution_request",
            resource_id=execution_request_id,
            payload={"reason": reason},
        )

    async def record_execution_started(
        self,
        *,
        user_id: UUID,
        execution_request_id: UUID,
        session_id: UUID | None = None,
    ) -> DomainEvent:
        if session_id is None:
            session = await self.repo.get_active_session_for_execution(execution_request_id)
            session_id = session.id if session else None

        return await self.publish_event(
            event_type=EXECUTION_STARTED,
            user_id=user_id,
            session_id=session_id,
            resource_type="execution_request",
            resource_id=execution_request_id,
        )

    async def record_suspicious_activity(
        self,
        *,
        user_id: UUID,
        session_id: UUID | None,
        description: str,
        metadata: dict | None = None,
    ) -> DomainEvent:
        return await self.publish_event(
            event_type=SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            session_id=session_id,
            severity="critical",
            payload={"description": description, **(metadata or {})},
        )

    async def get_session(
        self,
        session_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> MonitoringSession:
        return await self._get_session_for_access(
            session_id, user_id=user_id, can_read_all=can_read_all
        )

    async def list_sessions(
        self,
        *,
        user_id: UUID,
        can_read_all: bool,
        status_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[MonitoringSession], int]:
        owner_id = None if can_read_all else user_id
        sessions = await self.repo.list_sessions(
            user_id=owner_id, status=status_filter, limit=limit, offset=offset
        )
        total = await self.repo.count_sessions(user_id=owner_id, status=status_filter)
        return sessions, total

    async def list_events(
        self,
        *,
        session_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DomainEvent], int]:
        events = await self.repo.list_domain_events(
            session_id=session_id, event_type=event_type, limit=limit, offset=offset
        )
        total = await self.repo.count_domain_events(
            session_id=session_id, event_type=event_type
        )
        return events, total

    async def get_or_open_session_for_execution(
        self,
        *,
        user_id: UUID,
        execution_request_id: UUID,
    ) -> MonitoringSession:
        return await self.open_session(
            user_id=user_id,
            execution_request_id=execution_request_id,
        )

    async def _get_session_for_access(
        self,
        session_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> MonitoringSession:
        if can_read_all:
            session = await self.repo.get_session(session_id)
        else:
            session = await self.repo.get_session_for_user(session_id, user_id)

        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Monitoring session not found",
            )
        return session

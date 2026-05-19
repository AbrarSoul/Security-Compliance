"""Real-time monitoring pipeline APIs (Sprint 3 Step 2)."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import (
    MONITORING_MANAGE,
    MONITORING_PUBLISH,
    MONITORING_READ,
    MONITORING_READ_ALL,
)
from app.db.session import get_db
from app.schemas.monitoring import (
    DomainEventListResponse,
    DomainEventResponse,
    MonitoringSessionListResponse,
    MonitoringSessionResponse,
    MonitoringStatusResponse,
    OpenMonitoringSessionRequest,
    PublishMonitoringEventRequest,
)
from app.services.events.pubsub import monitoring_pubsub
from app.services.monitoring.monitoring_service import MonitoringService
from app.core.config import get_settings
from app.workers.outbox_worker import OutboxWorker
from app.workers.runtime import outbox_worker

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


def get_monitoring_service(db: AsyncSession = Depends(get_db)) -> MonitoringService:
    return MonitoringService(db)


def get_outbox_worker() -> OutboxWorker:
    return outbox_worker


@router.get("/status", response_model=MonitoringStatusResponse)
async def monitoring_status(
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: MonitoringService = Depends(get_monitoring_service),
    worker: OutboxWorker = Depends(get_outbox_worker),
):
    can_read_all = auth.has_permission(MONITORING_READ_ALL)
    active_count = await service.repo.count_sessions(
        user_id=None if can_read_all else auth.user.id,
        status="active",
    )
    pending = await worker.pending_count()
    settings = get_settings()
    return MonitoringStatusResponse(
        active_sessions=active_count,
        outbox_pending=pending,
        outbox_worker_enabled=settings.monitoring_outbox_worker_enabled,
        outbox_poll_seconds=settings.monitoring_outbox_poll_seconds,
    )


@router.post(
    "/sessions",
    response_model=MonitoringSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def open_session(
    body: OpenMonitoringSessionRequest,
    auth: AuthContext = Depends(require_permission(MONITORING_MANAGE)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    session = await service.open_session(
        user_id=auth.user.id,
        execution_request_id=body.execution_request_id,
        metadata=body.metadata,
    )
    return MonitoringSessionResponse.model_validate(session)


@router.get("/sessions", response_model=MonitoringSessionListResponse)
async def list_sessions(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    can_read_all = auth.has_permission(MONITORING_READ_ALL)
    sessions, total = await service.list_sessions(
        user_id=auth.user.id,
        can_read_all=can_read_all,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return MonitoringSessionListResponse(
        items=[MonitoringSessionResponse.model_validate(s) for s in sessions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=MonitoringSessionResponse)
async def get_session(
    session_id: UUID,
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    session = await service.get_session(
        session_id,
        user_id=auth.user.id,
        can_read_all=auth.has_permission(MONITORING_READ_ALL),
    )
    return MonitoringSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/close", response_model=MonitoringSessionResponse)
async def close_session(
    session_id: UUID,
    auth: AuthContext = Depends(require_permission(MONITORING_MANAGE)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    session = await service.close_session(
        session_id,
        user_id=auth.user.id,
        can_manage_all=auth.has_permission(MONITORING_READ_ALL),
    )
    return MonitoringSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}/events", response_model=DomainEventListResponse)
async def list_session_events(
    session_id: UUID,
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    await service.get_session(
        session_id,
        user_id=auth.user.id,
        can_read_all=auth.has_permission(MONITORING_READ_ALL),
    )
    events, total = await service.list_events(
        session_id=session_id, event_type=event_type, limit=limit, offset=offset
    )
    return DomainEventListResponse(
        items=[DomainEventResponse.model_validate(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/events", response_model=DomainEventListResponse)
async def list_events(
    session_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    if session_id is not None:
        await service.get_session(
            session_id,
            user_id=auth.user.id,
            can_read_all=auth.has_permission(MONITORING_READ_ALL),
        )
    events, total = await service.list_events(
        session_id=session_id, event_type=event_type, limit=limit, offset=offset
    )
    return DomainEventListResponse(
        items=[DomainEventResponse.model_validate(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/events", response_model=DomainEventResponse, status_code=status.HTTP_201_CREATED)
async def publish_event(
    body: PublishMonitoringEventRequest,
    auth: AuthContext = Depends(require_permission(MONITORING_PUBLISH)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    event = await service.publish_event(
        event_type=body.event_type,
        user_id=auth.user.id,
        session_id=body.session_id,
        payload=body.payload,
        severity=body.severity,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        correlation_id=body.correlation_id,
        source=body.source,
    )
    return DomainEventResponse.model_validate(event)


@router.get("/sessions/{session_id}/stream")
async def stream_session_events(
    session_id: UUID,
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: MonitoringService = Depends(get_monitoring_service),
):
    await service.get_session(
        session_id,
        user_id=auth.user.id,
        can_read_all=auth.has_permission(MONITORING_READ_ALL),
    )
    queue = await monitoring_pubsub.subscribe(session_id=session_id)

    async def event_generator():
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await monitoring_pubsub.unsubscribe(queue, session_id=session_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

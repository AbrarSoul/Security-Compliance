"""Alerts and notification APIs (Sprint 3 Step 6)."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import (
    NOTIFICATION_MANAGE,
    NOTIFICATION_READ,
    NOTIFICATION_READ_ALL,
)
from app.db.session import get_db
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notifications import (
    MarkAllReadResponse,
    MarkReadResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notifications.pubsub import notification_pubsub

router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_notification_repo(db: AsyncSession = Depends(get_db)) -> NotificationRepository:
    return NotificationRepository(db)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    unread_only: bool = Query(default=False),
    notification_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user_id: UUID | None = Query(default=None),
    auth: AuthContext = Depends(require_permission(NOTIFICATION_READ)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    target_user = auth.user.id
    if user_id is not None and user_id != auth.user.id:
        if not auth.has_permission(NOTIFICATION_READ_ALL):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        target_user = user_id

    items, total = await repo.list_for_user(
        target_user,
        unread_only=unread_only,
        notification_type=notification_type,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    unread = await repo.count_unread(target_user)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    auth: AuthContext = Depends(require_permission(NOTIFICATION_READ)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    count = await repo.count_unread(auth.user.id)
    return UnreadCountResponse(unread_count=count)


@router.get("/stream/alerts")
async def stream_dashboard_alerts(
    auth: AuthContext = Depends(require_any_permission(NOTIFICATION_READ, NOTIFICATION_READ_ALL)),
):
    admin_stream = auth.has_permission(NOTIFICATION_READ_ALL)
    queue = await notification_pubsub.subscribe(
        None if admin_stream else auth.user.id,
        admin_stream=admin_stream,
    )

    async def event_generator():
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            await notification_pubsub.unsubscribe(
                queue,
                None if admin_stream else auth.user.id,
                admin_stream=admin_stream,
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/history", response_model=NotificationListResponse)
async def notification_history(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_permission(NOTIFICATION_READ)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    items, total = await repo.list_for_user(auth.user.id, limit=limit, offset=offset)
    unread = await repo.count_unread(auth.user.id)
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(n) for n in items],
        total=total,
        unread_count=unread,
    )


@router.get("/preferences/me", response_model=NotificationPreferenceResponse)
async def get_preferences(
    auth: AuthContext = Depends(require_permission(NOTIFICATION_MANAGE)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    prefs = await repo.get_or_create_preferences(auth.user.id)
    return NotificationPreferenceResponse.model_validate(prefs)


@router.patch("/preferences/me", response_model=NotificationPreferenceResponse)
async def update_preferences(
    body: NotificationPreferenceUpdate,
    auth: AuthContext = Depends(require_permission(NOTIFICATION_MANAGE)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    prefs = await repo.get_or_create_preferences(auth.user.id)
    updated = await repo.update_preferences(
        prefs, **body.model_dump(exclude_unset=True)
    )
    return NotificationPreferenceResponse.model_validate(updated)


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: UUID,
    auth: AuthContext = Depends(require_permission(NOTIFICATION_READ)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    row = await repo.get_by_id(notification_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    if row.user_id != auth.user.id and not auth.has_permission(NOTIFICATION_READ_ALL):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return NotificationResponse.model_validate(row)


@router.post("/{notification_id}/read", response_model=MarkReadResponse)
async def mark_notification_read(
    notification_id: UUID,
    auth: AuthContext = Depends(require_permission(NOTIFICATION_READ)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    row = await repo.mark_read(notification_id, auth.user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return MarkReadResponse(id=row.id, is_read=row.is_read, read_at=row.read_at)


@router.post("/read-all", response_model=MarkAllReadResponse)
async def mark_all_read(
    auth: AuthContext = Depends(require_permission(NOTIFICATION_READ)),
    repo: NotificationRepository = Depends(get_notification_repo),
):
    updated = await repo.mark_all_read(auth.user.id)
    return MarkAllReadResponse(updated=updated)


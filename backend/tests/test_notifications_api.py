"""API and pipeline tests for notifications (Sprint 3 Step 6)."""

import pytest
from httpx import AsyncClient
from app.db.session import AsyncSessionLocal
from app.services.events.constants import PROMPT_BLOCKED, PROMPT_SUBMITTED
from app.services.events.outbox_processor import OutboxProcessor
from app.services.notifications.constants import TYPE_PROMPT_BLOCKED
from app.services.notifications.notification_service import NotificationService

from tests.helpers.integration import (
    login_user,
    signup_user,
    skip_if_no_db,
    unique_email,
)


async def _token(client: AsyncClient, email: str | None = None) -> str:
    data = await signup_user(client, email=email or unique_email("notify"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


async def _process_outbox() -> int:
    processor = OutboxProcessor(AsyncSessionLocal, batch_size=50)
    return await processor.process_batch()


@pytest.mark.asyncio
async def test_notification_preferences_defaults(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/notifications/preferences/me", headers=headers)
    skip_if_no_db(resp)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["in_app_enabled"] is True
    assert body["email_enabled"] is True
    assert body["notify_prompt_blocked"] is True


@pytest.mark.asyncio
async def test_prompt_blocked_creates_notification_via_outbox(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    open_resp = await client.post(
        "/api/v1/monitoring/sessions",
        json={},
        headers=headers,
    )
    skip_if_no_db(open_resp)
    session_id = open_resp.json()["id"]

    pub_resp = await client.post(
        "/api/v1/monitoring/events",
        json={
            "event_type": PROMPT_BLOCKED,
            "session_id": session_id,
            "severity": "high",
            "payload": {"reason": "blocked in test"},
        },
        headers=headers,
    )
    assert pub_resp.status_code == 201, pub_resp.text

    processed = await _process_outbox()
    assert processed >= 1

    list_resp = await client.get("/api/v1/notifications", headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    data = list_resp.json()
    assert data["total"] >= 1
    assert data["unread_count"] >= 1
    types = {item["notification_type"] for item in data["items"]}
    assert TYPE_PROMPT_BLOCKED in types


@pytest.mark.asyncio
async def test_mark_read_and_unread_count(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    open_resp = await client.post(
        "/api/v1/monitoring/sessions", json={}, headers=headers
    )
    skip_if_no_db(open_resp)
    session_id = open_resp.json()["id"]

    await client.post(
        "/api/v1/monitoring/events",
        json={
            "event_type": PROMPT_SUBMITTED,
            "session_id": session_id,
            "payload": {},
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/monitoring/events",
        json={
            "event_type": PROMPT_BLOCKED,
            "session_id": session_id,
            "severity": "warning",
            "payload": {"reason": "test read"},
        },
        headers=headers,
    )
    await _process_outbox()

    list_resp = await client.get("/api/v1/notifications", headers=headers)
    assert list_resp.status_code == 200
    notif_id = list_resp.json()["items"][0]["id"]

    read_resp = await client.post(
        f"/api/v1/notifications/{notif_id}/read",
        headers=headers,
    )
    assert read_resp.status_code == 200
    assert read_resp.json()["is_read"] is True

    count_resp = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count_resp.status_code == 200


@pytest.mark.asyncio
async def test_notification_service_direct():
    async with AsyncSessionLocal() as db:
        from app.models.user import User
        from app.auth.security import hash_password

        user = User(
            email=unique_email("notif-svc"),
            password_hash=hash_password("TestPass123!"),
            full_name="Notify Test",
        )
        db.add(user)
        await db.flush()

        service = NotificationService(db)
        created = await service.process_domain_event(
            {
                "event_type": PROMPT_BLOCKED,
                "user_id": str(user.id),
                "severity": "high",
                "payload": {"reason": "direct"},
            }
        )
        await db.commit()
        assert len(created) >= 1
        assert created[0].notification_type == TYPE_PROMPT_BLOCKED

"""Sprint 3 Step 2 — monitoring pipeline tests."""

import pytest
from httpx import AsyncClient

from app.services.events.constants import EXECUTION_BLOCKED, PROMPT_SUBMITTED
from app.services.events.types import DomainEventEnvelope

from tests.helpers.integration import (
    STRONG_PASSWORD,
    login_user,
    signup_user,
    skip_if_no_db,
    unique_email,
)


async def _token(client: AsyncClient, email: str | None = None) -> str:
    data = await signup_user(client, email=email or unique_email("monitor"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


def test_domain_event_envelope_serializes():
    envelope = DomainEventEnvelope(
        event_type=PROMPT_SUBMITTED,
        payload={"prompt_ref": "p1"},
    )
    data = envelope.to_dict()
    assert data["event_type"] == PROMPT_SUBMITTED
    assert data["payload"]["prompt_ref"] == "p1"
    assert data["event_id"]


@pytest.mark.asyncio
async def test_monitoring_api_open_session_and_publish(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    open_resp = await client.post(
        "/api/v1/monitoring/sessions",
        json={},
        headers=headers,
    )
    skip_if_no_db(open_resp)
    assert open_resp.status_code == 201, open_resp.text
    session_id = open_resp.json()["id"]

    pub_resp = await client.post(
        "/api/v1/monitoring/events",
        json={
            "event_type": PROMPT_SUBMITTED,
            "session_id": session_id,
            "payload": {"prompt_ref": "api-test"},
        },
        headers=headers,
    )
    assert pub_resp.status_code == 201, pub_resp.text
    assert pub_resp.json()["event_type"] == PROMPT_SUBMITTED

    events_resp = await client.get(
        f"/api/v1/monitoring/sessions/{session_id}/events",
        headers=headers,
    )
    assert events_resp.status_code == 200
    types = {e["event_type"] for e in events_resp.json()["items"]}
    assert PROMPT_SUBMITTED in types

    assert events_resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_monitoring_status_endpoint(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/monitoring/status", headers=headers)
    skip_if_no_db(resp)
    assert resp.status_code == 200
    body = resp.json()
    assert "active_sessions" in body
    assert "outbox_pending" in body


@pytest.mark.asyncio
async def test_publish_requires_session_owner(client: AsyncClient):
    token_a = await _token(client, unique_email("mona"))
    token_b = await _token(client, unique_email("monb"))

    open_resp = await client.post(
        "/api/v1/monitoring/sessions",
        json={},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    skip_if_no_db(open_resp)
    session_id = open_resp.json()["id"]

    forbidden = await client.post(
        "/api/v1/monitoring/events",
        json={"event_type": PROMPT_SUBMITTED, "session_id": session_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_close_session(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    open_resp = await client.post(
        "/api/v1/monitoring/sessions", json={}, headers=headers
    )
    skip_if_no_db(open_resp)
    session_id = open_resp.json()["id"]

    close_resp = await client.post(
        f"/api/v1/monitoring/sessions/{session_id}/close",
        headers=headers,
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"


@pytest.mark.asyncio
async def test_list_global_events(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/monitoring/events", headers=headers)
    skip_if_no_db(resp)
    assert resp.status_code == 200
    assert "items" in resp.json()


@pytest.mark.asyncio
async def test_outbox_processor_via_blocked_event_type_constant():
    """Sanity: blocked event type is part of alert set used by status handler."""
    from app.services.events.handlers.monitoring_status import _ALERT_EVENT_TYPES

    assert EXECUTION_BLOCKED in _ALERT_EVENT_TYPES

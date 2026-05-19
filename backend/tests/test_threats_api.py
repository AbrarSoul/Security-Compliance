"""Threat detection API tests (Sprint 3 Step 9)."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_user, skip_if_no_db, unique_email


async def _token(client: AsyncClient) -> str:
    data = await signup_user(client, email=unique_email("threat"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_threat_dashboard_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/threats/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_threat_dashboard(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/threats/dashboard", headers=headers)
    skip_if_no_db(resp)
    if resp.status_code == 403:
        pytest.skip("User lacks threat:read")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "security_posture" in body
    assert "open_threats" in body


@pytest.mark.asyncio
async def test_threat_events_and_behavior(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    events = await client.get("/api/v1/threats/events", headers=headers)
    skip_if_no_db(events)
    if events.status_code == 403:
        pytest.skip("User lacks threat:read")
    assert events.status_code == 200

    behavior = await client.get("/api/v1/threats/behavior", headers=headers)
    assert behavior.status_code == 200


@pytest.mark.asyncio
async def test_run_threat_detection(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/threats/detect", headers=headers)
    skip_if_no_db(resp)
    if resp.status_code == 403:
        pytest.skip("User lacks threat:manage (admin)")
    assert resp.status_code == 201, resp.text

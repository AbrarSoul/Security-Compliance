"""
Sprint 3 module integration tests (monitoring, notifications, analytics, gaps, threats).

Run: pytest -m sprint3 tests/test_sprint3_integration.py -v
"""

import pytest
from httpx import AsyncClient

from app.db.session import AsyncSessionLocal
from app.services.events.outbox_processor import OutboxProcessor
from app.services.events.handlers.registry import build_default_registry

from tests.helpers.integration import (
    auth_headers,
    signup_user,
    signup_with_role,
    skip_if_no_db,
)
from tests.helpers.sprint3 import open_monitoring_session, process_outbox

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.sprint3]


@pytest.mark.sprint3
async def test_outbox_registry_includes_all_handlers():
    registry = build_default_registry()
    assert "prompt.blocked" in registry._handlers
    assert "*" in registry._handlers


@pytest.mark.sprint3
async def test_monitoring_status_and_events(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    status = await client.get("/api/v1/monitoring/status", headers=headers)
    skip_if_no_db(status)
    assert status.status_code == 200
    assert "active_sessions" in status.json()

    events = await client.get("/api/v1/monitoring/events", headers=headers)
    assert events.status_code == 200


@pytest.mark.sprint3
async def test_notification_preferences_roundtrip(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    get_resp = await client.get("/api/v1/notifications/preferences/me", headers=headers)
    skip_if_no_db(get_resp)
    if get_resp.status_code == 403:
        pytest.skip("User lacks notification:manage")
    assert get_resp.status_code == 200

    patch = await client.patch(
        "/api/v1/notifications/preferences/me",
        headers=headers,
        json={"email_min_severity": "high"},
    )
    assert patch.status_code == 200
    assert patch.json()["email_min_severity"] == "high"


@pytest.mark.sprint3
async def test_analytics_endpoints_bundle(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    paths = [
        "/api/v1/analytics/summary?days=30",
        "/api/v1/analytics/trends/executions?days=14",
        "/api/v1/analytics/trends/risk?days=14",
        "/api/v1/analytics/trends/violations?days=14",
        "/api/v1/analytics/prompt-monitoring?days=30",
        "/api/v1/analytics/output-leakage?days=30",
        "/api/v1/analytics/violations/realtime?days=7",
    ]
    for path in paths:
        resp = await client.get(path, headers=headers)
        skip_if_no_db(resp)
        if resp.status_code == 403:
            pytest.skip("User lacks analytics:read")
        assert resp.status_code == 200, f"{path}: {resp.text}"


@pytest.mark.sprint3
async def test_gaps_and_threats_read_endpoints(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    for path in ("/api/v1/gaps/dashboard", "/api/v1/threats/dashboard"):
        resp = await client.get(path, headers=headers)
        skip_if_no_db(resp)
        if resp.status_code == 403:
            continue
        assert resp.status_code == 200, path


@pytest.mark.sprint3
async def test_auditor_read_all_scope(client: AsyncClient):
    tokens = await signup_with_role(client, "auditor")
    headers = auth_headers(tokens["access_token"])

    analytics = await client.get("/api/v1/analytics/dashboard", headers=headers)
    skip_if_no_db(analytics)
    if analytics.status_code == 403:
        pytest.skip("Auditor permissions not seeded")
    assert analytics.status_code == 200
    assert analytics.json()["summary"]["scope"] == "organization"


@pytest.mark.sprint3
async def test_outbox_processor_idempotent_empty():
    processor = OutboxProcessor(AsyncSessionLocal)
    assert await processor.process_batch() == 0


@pytest.mark.sprint3
async def test_output_scan_api(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    resp = await client.post(
        "/api/v1/monitoring/outputs/scan",
        headers=headers,
        json={"output": "Hello, this is a safe summary."},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 201, resp.text
    assert resp.json()["decision"] in ("allow", "warn", "block")

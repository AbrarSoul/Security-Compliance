"""Analytics dashboard API tests (Sprint 3 Step 7)."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_user, skip_if_no_db, unique_email


async def _token(client: AsyncClient, email: str | None = None) -> str:
    data = await signup_user(client, email=email or unique_email("analytics"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_analytics_summary_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/analytics/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_analytics_summary_and_dashboard(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    summary = await client.get("/api/v1/analytics/summary?days=30", headers=headers)
    skip_if_no_db(summary)
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert "violation_events" in body
    assert "blocked_executions" in body
    assert body["scope"] in ("user", "organization")

    dash = await client.get("/api/v1/analytics/dashboard?days=7", headers=headers)
    assert dash.status_code == 200, dash.text
    data = dash.json()
    assert "summary" in data
    assert "execution_trend" in data
    assert "prompt_stats" in data
    assert "realtime_violations" in data


@pytest.mark.asyncio
async def test_analytics_trend_endpoints(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for path in (
        "/api/v1/analytics/trends/executions",
        "/api/v1/analytics/trends/risk",
        "/api/v1/analytics/trends/violations",
        "/api/v1/analytics/trends/policy-violations",
    ):
        resp = await client.get(f"{path}?days=14", headers=headers)
        skip_if_no_db(resp)
        assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_analytics_monitoring_endpoints(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    for path in (
        "/api/v1/analytics/prompt-monitoring",
        "/api/v1/analytics/output-leakage",
        "/api/v1/analytics/blocked-executions",
        "/api/v1/analytics/violations/realtime",
        "/api/v1/analytics/high-risk/users",
        "/api/v1/analytics/high-risk/models",
    ):
        resp = await client.get(f"{path}?days=30", headers=headers)
        skip_if_no_db(resp)
        assert resp.status_code == 200, resp.text

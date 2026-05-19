"""Compliance gap analysis API tests (Sprint 3 Step 8)."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_user, skip_if_no_db, unique_email


async def _admin_token(client: AsyncClient) -> str | None:
    """Signup user; gap:analyze requires admin role from migration."""
    data = await signup_user(client, email=unique_email("gapadmin"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_gaps_dashboard_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/gaps/dashboard")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_gaps_dashboard_empty(client: AsyncClient):
    token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/gaps/dashboard", headers=headers)
    skip_if_no_db(resp)
    if resp.status_code == 403:
        pytest.skip("User lacks gap:read permission")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "posture_score" in body
    assert "open_gaps" in body


@pytest.mark.asyncio
async def test_run_gap_analysis(client: AsyncClient):
    token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/gaps/analyze", headers=headers)
    skip_if_no_db(resp)
    if resp.status_code == 403:
        pytest.skip("User lacks gap:analyze permission (admin only)")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "gaps_found" in body
    assert "gaps" in body

    dash = await client.get("/api/v1/gaps/dashboard", headers=headers)
    assert dash.status_code == 200
    assert dash.json()["latest_run"] is not None


@pytest.mark.asyncio
async def test_gap_list_and_history(client: AsyncClient):
    token = await _admin_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/gaps/analyze", headers=headers)

    list_resp = await client.get("/api/v1/gaps", headers=headers)
    skip_if_no_db(list_resp)
    if list_resp.status_code == 403:
        pytest.skip("User lacks gap:read")
    assert list_resp.status_code == 200

    hist = await client.get("/api/v1/gaps/history", headers=headers)
    assert hist.status_code == 200

    runs = await client.get("/api/v1/gaps/runs", headers=headers)
    assert runs.status_code == 200

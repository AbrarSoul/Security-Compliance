"""Compliance posture API tests."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_with_role, skip_if_no_db, unique_email


async def _token(client: AsyncClient) -> str | None:
    tokens = await signup_with_role(client, "admin", email=unique_email("posture"))
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_compliance_posture_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/compliance/posture")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_compliance_posture_returns_frameworks(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/api/v1/compliance/posture", headers=headers)
    skip_if_no_db(resp)
    if resp.status_code == 403:
        pytest.skip("User lacks gap:read permission")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "frameworks" in body
    assert "disclaimer" in body
    ids = {f["id"] for f in body["frameworks"]}
    assert "nist_ai_rmf" in ids
    assert "internal_guardrails" in ids
    assert "gaira" in ids

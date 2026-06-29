"""Tests for NIST AI RMF catalog and profile APIs."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_with_role, skip_if_no_db, unique_email


async def _headers(client: AsyncClient) -> dict[str, str]:
    tokens = await signup_with_role(client, "user", email=unique_email("nist"))
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.asyncio
async def test_nist_controls_catalog(client: AsyncClient):
    headers = await _headers(client)
    resp = await client.get("/api/v1/nist-ai-rmf/controls", headers=headers)
    skip_if_no_db(resp)
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0"
    assert body["control_count"] == 72
    assert len(body["controls"]) == 72
    assert body["profile"]["id"] == "complianceguard-operational-v1"
    functions = {c["function"] for c in body["controls"]}
    assert functions == {"GOVERN", "MAP", "MEASURE", "MANAGE"}


@pytest.mark.asyncio
async def test_nist_current_profile(client: AsyncClient):
    headers = await _headers(client)
    resp = await client.get("/api/v1/nist-ai-rmf/profile/current", headers=headers)
    skip_if_no_db(resp)
    assert resp.status_code == 200
    body = resp.json()
    assert body["framework_version"] == "1.0"
    assert body["summary"]["total"] == 72
    assert len(body["controls"]) == 72
    assert "alignment_score" in body
    assert "compliance_status" in body
    assert "violations" in body["summary"]
    assert "alignment_gaps" in body["summary"]
    assert "finding_kind" in body["controls"][0]
    assert "disclaimer" in body
    assert set(body["by_function"].keys()) == {"GOVERN", "MAP", "MEASURE", "MANAGE"}

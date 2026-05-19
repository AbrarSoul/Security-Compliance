"""API tests for output compliance scanning."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_user, skip_if_no_db, unique_email


async def _token(client: AsyncClient) -> str:
    data = await signup_user(client, email=unique_email("output"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_scan_output_blocks_secret_leak(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}
    output = "Use api_key=sk-live-abcdefghijklmnopqrstuvwxyz1234567890"

    resp = await client.post(
        "/api/v1/monitoring/outputs/scan",
        headers=headers,
        json={"output": output},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["decision"] == "block"
    assert body["can_display"] is False
    assert body["redacted_output"] == ""
    assert "[API_KEY_MASKED]" in body["masked_output"]


@pytest.mark.asyncio
async def test_scan_output_allow_clean(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/api/v1/monitoring/outputs/scan",
        headers=headers,
        json={"output": "The deployment completed successfully."},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 201
    assert resp.json()["decision"] == "allow"
    assert resp.json()["can_display"] is True


@pytest.mark.asyncio
async def test_get_and_list_output_scans(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post(
        "/api/v1/monitoring/outputs/scan",
        headers=headers,
        json={"output": "Patient name: Jane Doe, MRN 44521."},
    )
    skip_if_no_db(create)
    scan_id = create.json()["scan_id"]

    get_resp = await client.get(
        f"/api/v1/monitoring/outputs/scans/{scan_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200

    list_resp = await client.get(
        "/api/v1/monitoring/outputs/scans",
        headers=headers,
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1

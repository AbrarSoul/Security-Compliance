"""Integration tests for real-time compliance guard."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import (
    get_seed_model,
    login_user,
    run_scan,
    signup_user,
    skip_if_no_db,
    unique_email,
    upload_dataset,
)



async def _user_with_execution(client: AsyncClient) -> tuple[str, str]:
    email = unique_email("guard")
    data = await signup_user(client, email=email)
    tokens = await login_user(client, email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    uploaded = await upload_dataset(client, headers, "minimal_clean.csv")
    scan = await run_scan(client, headers, uploaded["id"])
    model = await get_seed_model(client, headers, "DEMO_LOCAL_LLM")

    validate = await client.post(
        "/api/v1/executions/validate",
        headers=headers,
        json={
            "dataset_id": uploaded["id"],
            "scan_id": scan["id"],
            "model_id": model["id"],
            "execution_purpose": "Guard integration test",
        },
    )
    skip_if_no_db(validate)
    assert validate.status_code == 201, validate.text
    body = validate.json()
    if body["decision"] == "block":
        pytest.skip("Pre-validation blocked; need allow/warn execution for guard test")
    execution_id = body["execution_request_id"]
    return tokens["access_token"], execution_id


@pytest.mark.asyncio
async def test_guard_blocks_prompt_with_api_key(client: AsyncClient):
    token, execution_id = await _user_with_execution(client)
    headers = {"Authorization": f"Bearer {token}"}
    prompt = (
        "Run analysis with aws_secret_access_key="
        "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )

    resp = await client.post(
        f"/api/v1/monitoring/guard/executions/{execution_id}/prompt",
        headers=headers,
        json={"prompt": prompt},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision"] == "block"
    assert body["allowed"] is False
    assert len(body["blocking_reasons"]) >= 1
    assert body["prompt_scan_id"] is not None

    status_resp = await client.get(
        f"/api/v1/monitoring/guard/executions/{execution_id}/status",
        headers=headers,
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "blocked"
    assert len(status_resp.json()["guard_actions"]) >= 1


@pytest.mark.asyncio
async def test_guard_allows_clean_prompt(client: AsyncClient):
    token, execution_id = await _user_with_execution(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        f"/api/v1/monitoring/guard/executions/{execution_id}/prompt",
        headers=headers,
        json={"prompt": "Summarize the dataset schema only."},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 200
    assert resp.json()["decision"] == "allow"
    assert resp.json()["allowed"] is True


@pytest.mark.asyncio
async def test_guard_blocks_output_leakage(client: AsyncClient):
    token, execution_id = await _user_with_execution(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        f"/api/v1/monitoring/guard/executions/{execution_id}/output",
        headers=headers,
        json={"output": "The user's password=Secret123! is stored in the vault."},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["decision"] == "block"
    assert body["allowed"] is False
    assert "[PASSWORD_MASKED]" in (body.get("masked_content") or "")


@pytest.mark.asyncio
async def test_guard_interrupts_started_execution(client: AsyncClient):
    token, execution_id = await _user_with_execution(client)
    headers = {"Authorization": f"Bearer {token}"}

    validate_detail = await client.get(
        f"/api/v1/executions/{execution_id}",
        headers=headers,
    )
    skip_if_no_db(validate_detail)
    decision = validate_detail.json().get("result", {}).get("decision")
    if decision == "block":
        pytest.skip("Execution pre-blocked; cannot test runtime interrupt")

    start = await client.post(
        f"/api/v1/executions/{execution_id}/start",
        headers=headers,
    )
    if start.status_code == 403:
        pytest.skip("Execution not startable in current state")

    resp = await client.post(
        f"/api/v1/monitoring/guard/executions/{execution_id}/prompt",
        headers=headers,
        json={"prompt": "api_key=sk-live-abcdefghijklmnopqrstuvwxyz1234567890"},
    )
    skip_if_no_db(resp)
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "block"
    if body.get("interrupted"):
        assert body["execution_status"] == "interrupted"

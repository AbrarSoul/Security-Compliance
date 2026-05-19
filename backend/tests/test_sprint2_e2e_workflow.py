"""
Sprint 2 end-to-end workflow integration tests.

Full pipeline: upload → scan → validate → (acknowledge) → start → audit logs.

Requires PostgreSQL with migrations 001–016 applied.
Run: pytest -m integration tests/test_sprint2_e2e_workflow.py
"""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import (
    auth_headers,
    get_seed_model,
    run_scan,
    signup_user,
    skip_if_no_db,
    upload_dataset,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.e2e]


async def _validate_execution(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    dataset_id: str,
    scan_id: str,
    model_id: str,
    purpose: str = "Sprint 2 E2E validation",
) -> dict:
    response = await client.post(
        "/api/v1/executions/validate",
        headers=headers,
        json={
            "dataset_id": dataset_id,
            "scan_id": scan_id,
            "model_id": model_id,
            "execution_purpose": purpose,
        },
    )
    skip_if_no_db(response)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.integration
async def test_full_workflow_safe_local_allow(client: AsyncClient):
    """Example: safe local model execution (email only + local model → allow or warn)."""
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    file_rec = await upload_dataset(client, headers, "safe_internal.csv")
    scan = await run_scan(client, headers, file_rec["id"])
    model = await get_seed_model(client, headers, "DEMO_LOCAL_LLM")

    result = await _validate_execution(
        client,
        headers,
        dataset_id=file_rec["id"],
        scan_id=scan["id"],
        model_id=model["id"],
        purpose="Safe local model training demo",
    )

    assert result["decision"] in ("allow", "warn")
    assert result["execution_request_id"]
    assert isinstance(result["triggered_rules"], list)
    assert isinstance(result["policy_violations"], list)
    assert isinstance(result["model_risks"], list)

    exec_id = result["execution_request_id"]
    status_resp = await client.get(f"/api/v1/executions/{exec_id}/status", headers=headers)
    assert status_resp.status_code == 200
    status_body = status_resp.json()
    assert status_body["decision"] == result["decision"]

    if result["decision"] == "allow" or status_body.get("can_start"):
        if status_body.get("requires_acknowledgement"):
            ack = await client.post(
                f"/api/v1/executions/{exec_id}/acknowledge-warning",
                headers=headers,
                json={"acknowledgement_note": "Accepted demo risk"},
            )
            assert ack.status_code == 200, ack.text

        start = await client.post(f"/api/v1/executions/{exec_id}/start", headers=headers)
        assert start.status_code == 200, start.text
        assert start.json()["status"] in ("started", "approved_after_warning")

    audit = await client.get(
        "/api/v1/audit-logs",
        headers=headers,
        params={"action_prefix": "execution", "limit": 20},
    )
    if audit.status_code == 403:
        pytest.skip("User role cannot read audit logs")
    assert audit.status_code == 200
    actions = {e["action"] for e in audit.json()["items"]}
    assert any("execution" in a for a in actions)


@pytest.mark.integration
async def test_workflow_blocked_external_api(client: AsyncClient):
    """Example: blocked external API execution (passwords + external model → block)."""
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    file_rec = await upload_dataset(client, headers, "blocked_passwords.csv")
    scan = await run_scan(client, headers, file_rec["id"])
    model = await get_seed_model(client, headers, "DEMO_EXTERNAL_API")

    result = await _validate_execution(
        client,
        headers,
        dataset_id=file_rec["id"],
        scan_id=scan["id"],
        model_id=model["id"],
        purpose="Blocked external API demo",
    )

    assert result["decision"] == "block"
    assert len(result["triggered_rules"]) >= 1 or len(result["policy_violations"]) >= 1

    exec_id = result["execution_request_id"]
    status_resp = await client.get(f"/api/v1/executions/{exec_id}/status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["can_start"] is False

    start = await client.post(f"/api/v1/executions/{exec_id}/start", headers=headers)
    assert start.status_code in (400, 403, 409), start.text


@pytest.mark.integration
async def test_workflow_warning_acknowledge_path(client: AsyncClient):
    """Example: warning-level execution may require acknowledgement before start."""
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    file_rec = await upload_dataset(client, headers, "warning_confidential.csv")
    scan = await run_scan(client, headers, file_rec["id"])
    model = await get_seed_model(client, headers, "DEMO_CLOUD_UNAPPROVED")

    result = await _validate_execution(
        client,
        headers,
        dataset_id=file_rec["id"],
        scan_id=scan["id"],
        model_id=model["id"],
        purpose="Warning path demo",
    )

    assert result["decision"] in ("allow", "warn", "block")
    exec_id = result["execution_request_id"]

    detail = await client.get(f"/api/v1/executions/{exec_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["execution_result"] is not None

    if result["decision"] == "warn":
        status = (await client.get(f"/api/v1/executions/{exec_id}/status", headers=headers)).json()
        if status.get("requires_acknowledgement"):
            ack = await client.post(
                f"/api/v1/executions/{exec_id}/acknowledge-warning",
                headers=headers,
                json={"acknowledgement_note": "Proceeding after review"},
            )
            assert ack.status_code == 200, ack.text


@pytest.mark.integration
async def test_upload_scan_validate_list_chain(client: AsyncClient):
    """Verify modules integrate: files → scans → executions list."""
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    file_rec = await upload_dataset(client, headers, "safe_internal.csv")
    scan = await run_scan(client, headers, file_rec["id"])
    model = await get_seed_model(client, headers, "DEMO_LOCAL_LLM")
    await _validate_execution(
        client,
        headers,
        dataset_id=file_rec["id"],
        scan_id=scan["id"],
        model_id=model["id"],
    )

    scans = await client.get("/api/v1/scans", headers=headers)
    assert scans.status_code == 200
    assert scans.json()["total"] >= 1

    executions = await client.get("/api/v1/executions", headers=headers)
    assert executions.status_code == 200
    assert executions.json()["total"] >= 1

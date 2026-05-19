"""
Sprint 2 API integration tests: RBAC, policies, rules, executions, audit, validation.

Run: pytest -m integration tests/test_sprint2_api_integration.py
"""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import (
    auth_headers,
    get_seed_model,
    run_scan,
    signup_user,
    signup_with_role,
    skip_if_no_db,
    upload_dataset,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


# --- Authentication & RBAC ---


@pytest.mark.integration
async def test_unauthenticated_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/policies")
    assert response.status_code == 401


@pytest.mark.integration
async def test_user_cannot_create_policy(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])
    response = await client.post(
        "/api/v1/policies",
        headers=headers,
        json={
            "name": "Forbidden Policy",
            "policy_type": "execution_policy",
            "thresholds": {"block_below": 40, "warn_below": 70},
        },
    )
    skip_if_no_db(response)
    assert response.status_code == 403


@pytest.mark.integration
async def test_admin_can_list_and_create_policy(client: AsyncClient):
    admin = await signup_with_role(client, "admin")
    headers = auth_headers(admin["access_token"])

    listing = await client.get("/api/v1/policies", headers=headers)
    skip_if_no_db(listing)
    assert listing.status_code == 200
    assert "items" in listing.json()

    create = await client.post(
        "/api/v1/policies",
        headers=headers,
        json={
            "name": f"Test Policy {admin['_email'][:8]}",
            "policy_type": "security_policy",
            "status": "draft",
            "thresholds": {"block_below": 30, "warn_below": 60},
        },
    )
    assert create.status_code == 201, create.text
    policy = create.json()
    assert policy["thresholds"]["block_below"] == 30

    activate = await client.post(f"/api/v1/policies/{policy['id']}/activate", headers=headers)
    assert activate.status_code == 200
    assert activate.json()["status"] == "active"


@pytest.mark.integration
async def test_auditor_reads_executions_not_start(client: AsyncClient):
    auditor = await signup_with_role(client, "auditor")
    headers = auth_headers(auditor["access_token"])

    listing = await client.get("/api/v1/executions", headers=headers)
    skip_if_no_db(listing)
    assert listing.status_code == 200

    start_fake = await client.post(
        "/api/v1/executions/00000000-0000-4000-8000-000000000099/start",
        headers=headers,
    )
    assert start_fake.status_code == 403


@pytest.mark.integration
async def test_auditor_reads_audit_logs(client: AsyncClient):
    auditor = await signup_with_role(client, "auditor")
    headers = auth_headers(auditor["access_token"])
    response = await client.get("/api/v1/audit-logs", headers=headers, params={"limit": 5})
    skip_if_no_db(response)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.integration
async def test_user_denied_audit_logs(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])
    response = await client.get("/api/v1/audit-logs", headers=headers)
    skip_if_no_db(response)
    assert response.status_code == 403


# --- Rules API ---


@pytest.mark.integration
async def test_rules_list_and_filter(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    all_rules = await client.get("/api/v1/rules", headers=headers)
    skip_if_no_db(all_rules)
    assert all_rules.status_code == 200
    assert all_rules.json()["total"] >= 5

    data_rules = await client.get(
        "/api/v1/rules", headers=headers, params={"category": "data"}
    )
    assert data_rules.status_code == 200
    for rule in data_rules.json()["items"]:
        assert rule["category"] == "data"


@pytest.mark.integration
async def test_admin_rule_enable_disable(client: AsyncClient):
    admin = await signup_with_role(client, "admin")
    headers = auth_headers(admin["access_token"])

    rules = await client.get("/api/v1/rules", headers=headers, params={"limit": 1})
    skip_if_no_db(rules)
    assert rules.status_code == 200
    if not rules.json()["items"]:
        pytest.skip("No rules seeded")
    rule_id = rules.json()["items"][0]["id"]

    disable = await client.post(f"/api/v1/rules/{rule_id}/disable", headers=headers)
    assert disable.status_code == 200
    assert disable.json()["is_enabled"] is False

    enable = await client.post(f"/api/v1/rules/{rule_id}/enable", headers=headers)
    assert enable.status_code == 200
    assert enable.json()["is_enabled"] is True


# --- Policies API ---


@pytest.mark.integration
async def test_policy_detail_includes_thresholds_and_rules(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    active = await client.get("/api/v1/policies/active", headers=headers)
    skip_if_no_db(active)
    assert active.status_code == 200
    items = active.json()["items"]
    if not items:
        pytest.skip("No active demo policies (run migration 016)")

    policy_id = items[0]["id"]
    detail = await client.get(f"/api/v1/policies/{policy_id}", headers=headers)
    assert detail.status_code == 200
    body = detail.json()
    assert "thresholds" in body
    assert "block_below" in body["thresholds"]
    assert isinstance(body["rules"], list)


# --- Execution validation & blocking ---


@pytest.mark.integration
async def test_execution_validate_invalid_scan_returns_400(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])
    file_rec = await upload_dataset(client, headers, "safe_internal.csv")

    response = await client.post(
        "/api/v1/executions/validate",
        headers=headers,
        json={
            "dataset_id": file_rec["id"],
            "scan_id": "00000000-0000-4000-8000-000000000099",
            "model_id": "00000000-0000-4000-8000-000000000099",
            "execution_purpose": "invalid",
        },
    )
    skip_if_no_db(response)
    assert response.status_code in (400, 404)


@pytest.mark.integration
async def test_execution_pagination(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])

    page = await client.get(
        "/api/v1/executions", headers=headers, params={"limit": 2, "offset": 0}
    )
    skip_if_no_db(page)
    assert page.status_code == 200
    body = page.json()
    assert body["limit"] == 2
    assert "items" in body


# --- Models API ---


@pytest.mark.integration
async def test_seed_models_present(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])
    local = await get_seed_model(client, headers, "DEMO_LOCAL_LLM")
    external = await get_seed_model(client, headers, "DEMO_EXTERNAL_API")
    assert local["model_type"] == "local_model"
    assert external["data_leaves_platform"] is True


@pytest.mark.integration
async def test_model_validation_endpoint(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])
    file_rec = await upload_dataset(client, headers, "safe_internal.csv")
    scan = await run_scan(client, headers, file_rec["id"])
    model = await get_seed_model(client, headers, "DEMO_LOCAL_LLM")

    response = await client.post(
        "/api/v1/models/validate",
        headers=headers,
        json={"scan_id": scan["id"], "model_id": model["id"]},
    )
    skip_if_no_db(response)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"] in ("allow", "warn", "block")
    assert "risk_score" in body


# --- API validation (error shape) ---


@pytest.mark.integration
async def test_validation_error_includes_detail(client: AsyncClient):
    user = await signup_user(client)
    headers = auth_headers(user["access_token"])
    response = await client.post(
        "/api/v1/executions/validate",
        headers=headers,
        json={"dataset_id": "not-a-uuid"},
    )
    skip_if_no_db(response)
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body or "error" in body

"""API tests for GAIRA assessment endpoints."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import login_user, signup_user, skip_if_no_db, unique_email


async def _token(client: AsyncClient) -> str:
    data = await signup_user(client, email=unique_email("gaira"))
    tokens = await login_user(client, data["_email"])
    return tokens["access_token"]


@pytest.mark.asyncio
async def test_gaira_framework_and_application_flow(client: AsyncClient):
    token = await _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    framework_resp = await client.get("/api/v1/gaira/framework", headers=headers)
    skip_if_no_db(framework_resp)
    assert framework_resp.status_code == 200
    body = framework_resp.json()
    assert body["version"]
    assert any(m["key"] == "gaira_light" for m in body["modules"])

    create_resp = await client.post(
        "/api/v1/gaira/applications",
        headers=headers,
        json={
            "name": "Project Alpha",
            "owner_name": "Peter Parker",
            "purpose": "Meeting transcription and summarization",
        },
    )
    assert create_resp.status_code == 201, create_resp.text
    app_id = create_resp.json()["id"]

    assessment_resp = await client.post(
        f"/api/v1/gaira/applications/{app_id}/assessments",
        headers=headers,
        json={"assessment_type": "ai_risk_levels"},
    )
    assert assessment_resp.status_code == 201, assessment_resp.text
    assessment_id = assessment_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/v1/gaira/assessments/{assessment_id}/answers",
        headers=headers,
        json={"answers": {"2.01": {"value": "Yes"}}},
    )
    assert patch_resp.status_code == 200

    compute_resp = await client.post(
        f"/api/v1/gaira/assessments/{assessment_id}/compute",
        headers=headers,
    )
    assert compute_resp.status_code == 200
    assert compute_resp.json()["computed_json"]["risk_level"] == "high"

    submit_resp = await client.post(
        f"/api/v1/gaira/assessments/{assessment_id}/submit",
        headers=headers,
        json={"overall_risk_level": "high", "proceed_decision": "Further review required"},
    )
    assert submit_resp.status_code == 200
    assert submit_resp.json()["status"] == "submitted"

    roaia_resp = await client.get("/api/v1/gaira/roaia", headers=headers)
    assert roaia_resp.status_code == 200
    assert roaia_resp.json()["total"] >= 1

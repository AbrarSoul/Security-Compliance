"""Tests for GAIRA AI application registration approval workflow."""

import pytest
from httpx import AsyncClient

from tests.helpers.integration import (
    approve_user,
    auth_headers,
    login_user,
    signup_user,
    signup_with_role,
    skip_if_no_db,
    unique_email,
)


async def _register_application(client: AsyncClient, headers: dict) -> str:
    response = await client.post(
        "/api/v1/gaira/applications",
        headers=headers,
        json={
            "name": "Registration Workflow App",
            "owner_name": "Test Owner",
            "purpose": "Testing registration approval",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["registration_status"] == "pending_auditor"
    assert body["is_active"] is False
    return body["id"]


@pytest.mark.asyncio
async def test_user_registration_requires_approval_before_assessment(client: AsyncClient):
    user = await signup_with_role(client, "user")
    user_headers = auth_headers((await login_user(client, user["_email"]))["access_token"])

    app_id = await _register_application(client, user_headers)

    assessment_resp = await client.post(
        f"/api/v1/gaira/applications/{app_id}/assessments",
        headers=user_headers,
        json={"assessment_type": "ai_risk_levels"},
    )
    skip_if_no_db(assessment_resp)
    assert assessment_resp.status_code == 400
    assert "approved" in assessment_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_registration_review_and_approval_flow(client: AsyncClient):
    user = await signup_with_role(client, "user")
    auditor = await signup_with_role(client, "auditor", email=unique_email("gaira-auditor"))
    admin = await signup_with_role(client, "admin", email=unique_email("gaira-admin"))

    user_headers = auth_headers((await login_user(client, user["_email"]))["access_token"])
    auditor_headers = auth_headers((await login_user(client, auditor["_email"]))["access_token"])
    admin_headers = auth_headers((await login_user(client, admin["_email"]))["access_token"])

    app_id = await _register_application(client, user_headers)

    pending_auditor = await client.get(
        "/api/v1/gaira/applications/pending-auditor",
        headers=auditor_headers,
    )
    skip_if_no_db(pending_auditor)
    assert pending_auditor.status_code == 200
    assert pending_auditor.json()["total"] >= 1

    feedback_resp = await client.post(
        f"/api/v1/gaira/applications/{app_id}/auditor-feedback",
        headers=auditor_headers,
        json={"feedback": "Purpose is clear. Recommend approval with standard GAIRA triage."},
    )
    assert feedback_resp.status_code == 200, feedback_resp.text
    assert feedback_resp.json()["application"]["registration_status"] == "pending_admin"

    pending_admin = await client.get(
        "/api/v1/gaira/applications/pending-admin",
        headers=admin_headers,
    )
    assert pending_admin.status_code == 200
    assert any(item["id"] == app_id for item in pending_admin.json()["items"])

    approve_resp = await client.post(
        f"/api/v1/gaira/applications/{app_id}/approve",
        headers=admin_headers,
    )
    assert approve_resp.status_code == 200, approve_resp.text
    approved = approve_resp.json()["application"]
    assert approved["registration_status"] == "approved"
    assert approved["is_active"] is True

    assessment_resp = await client.post(
        f"/api/v1/gaira/applications/{app_id}/assessments",
        headers=user_headers,
        json={"assessment_type": "ai_risk_levels"},
    )
    assert assessment_resp.status_code == 201, assessment_resp.text


@pytest.mark.asyncio
async def test_admin_created_application_is_auto_approved(client: AsyncClient):
    admin = await signup_with_role(client, "admin", email=unique_email("gaira-admin-auto"))
    admin_headers = auth_headers((await login_user(client, admin["_email"]))["access_token"])

    create_resp = await client.post(
        "/api/v1/gaira/applications",
        headers=admin_headers,
        json={"name": "Admin Auto Approved", "purpose": "Direct admin registration"},
    )
    skip_if_no_db(create_resp)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["registration_status"] == "approved"
    assert body["is_active"] is True

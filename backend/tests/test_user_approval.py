"""Tests for registration approval workflow."""

import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")

from app.main import app
from tests.helpers.integration import STRONG_PASSWORD, approve_user, unique_email

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _skip_if_no_db(response):
    if response.status_code >= 500:
        pytest.skip("Database not available")


@pytest.mark.integration
async def test_signup_pending_cannot_login_until_approved(client: AsyncClient):
    email = unique_email("pending")
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": STRONG_PASSWORD, "full_name": "Pending User"},
    )
    _skip_if_no_db(signup)
    assert signup.status_code == 201
    body = signup.json()
    assert body["approval_status"] == "pending"
    assert "access_token" not in body

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": STRONG_PASSWORD},
    )
    assert login.status_code == 403
    assert "pending" in login.json()["detail"].lower()

    await approve_user(email, "user")

    login_ok = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": STRONG_PASSWORD},
    )
    assert login_ok.status_code == 200


@pytest.mark.integration
async def test_admin_can_approve_with_role(client: AsyncClient):
    email = unique_email("approve")
    await client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": STRONG_PASSWORD},
    )

    admin_email = unique_email("admin")
    admin_signup = await client.post(
        "/api/v1/auth/signup",
        json={"email": admin_email, "password": STRONG_PASSWORD},
    )
    _skip_if_no_db(admin_signup)
    await approve_user(admin_email, "admin")
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": STRONG_PASSWORD},
    )
    admin_token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    pending = await client.get("/api/v1/users/pending", headers=headers)
    assert pending.status_code == 200
    target = next(item for item in pending.json()["items"] if item["email"] == email)

    approved = await client.post(
        f"/api/v1/users/{target['id']}/approve",
        headers=headers,
        json={"role": "auditor"},
    )
    assert approved.status_code == 200

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": STRONG_PASSWORD},
    )
    assert login.status_code == 200
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert "auditor" in me.json()["roles"]

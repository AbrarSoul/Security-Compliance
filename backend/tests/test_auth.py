import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")

from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture
def strong_password() -> str:
    return "SecurePass123"


def _skip_if_no_db(response):
    if response.status_code >= 500:
        pytest.skip("Database not available")


@pytest.mark.integration
async def test_signup_login_me_logout_flow(client: AsyncClient, strong_password: str):
    """Full auth flow against PostgreSQL. Skipped if DB unavailable."""
    email = _unique_email()

    try:
        signup = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": strong_password, "full_name": "Test User"},
        )
    except OSError:
        pytest.skip("Database not available")
    _skip_if_no_db(signup)
    assert signup.status_code == 201, signup.text
    pending = signup.json()
    assert pending["approval_status"] == "pending"
    assert "message" in pending

    from tests.helpers.integration import approve_user

    await approve_user(email, "user")

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": strong_password},
    )
    assert login.status_code == 200, login.text
    tokens = login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["user"]["email"] == email

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == email

    profile = await client.get("/api/v1/protected/profile", headers=headers)
    assert profile.status_code == 200

    unauth = await client.get("/api/v1/auth/me")
    assert unauth.status_code == 401

    logout = await client.post(
        "/api/v1/auth/logout",
        headers=headers,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 204

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": strong_password},
    )
    assert login.status_code == 200
    new_tokens = login.json()

    refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": new_tokens["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()


async def test_signup_weak_password_rejected(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/signup",
        json={"email": _unique_email(), "password": "weak"},
    )
    assert response.status_code == 422


async def test_login_invalid_credentials(client: AsyncClient):
    try:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "WrongPass123"},
        )
    except OSError:
        pytest.skip("Database not available")
    _skip_if_no_db(response)
    assert response.status_code == 401


async def test_protected_route_requires_token(client: AsyncClient):
    response = await client.get("/api/v1/protected/status")
    assert response.status_code == 401

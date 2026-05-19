import os
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")

from app.db.session import AsyncSessionLocal
from app.main import app
from app.repositories.user_repository import UserRepository
from app.services.rbac_service import RbacService

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _unique_email() -> str:
    return f"audit-{uuid.uuid4().hex[:8]}@example.com"


def _strong_password() -> str:
    return "SecurePass123"


def _skip_if_no_db(response):
    if response.status_code >= 500:
        pytest.skip("Database not available (run migrations through 009)")


@pytest.mark.integration
async def test_user_cannot_list_audit_logs(client: AsyncClient):
    email = _unique_email()
    try:
        signup = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": _strong_password()},
        )
    except OSError:
        pytest.skip("Database not available")
    _skip_if_no_db(signup)
    token = signup.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/audit-logs", headers=headers)
    assert response.status_code == 403


@pytest.mark.integration
async def test_auditor_can_list_audit_logs_after_signup(client: AsyncClient):
    email = _unique_email()
    try:
        signup = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": _strong_password()},
        )
    except OSError:
        pytest.skip("Database not available")
    _skip_if_no_db(signup)

    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        await RbacService(db).assign_role(user.id, "auditor")
        await db.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _strong_password()},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    logs = await client.get("/api/v1/audit-logs", headers=headers)
    assert logs.status_code == 200
    body = logs.json()
    assert "items" in body
    assert body["total"] >= 1
    actions = {item["action"] for item in body["items"]}
    assert "auth.signup" in actions or "auth.login" in actions

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
    return f"rbac-{uuid.uuid4().hex[:8]}@example.com"


def _strong_password() -> str:
    return "SecurePass123"


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _skip_if_no_db(response):
    if response.status_code >= 500:
        pytest.skip("Database not available (run migrations 007 and 008)")


async def _signup(client: AsyncClient, email: str | None = None) -> dict:
    email = email or _unique_email()
    try:
        response = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": _strong_password(), "full_name": "RBAC Test"},
        )
    except OSError:
        pytest.skip("Database not available")
    _skip_if_no_db(response)
    assert response.status_code == 201, response.text
    return response.json()


async def _assign_role(email: str, role_name: str) -> None:
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        assert user is not None
        await RbacService(db).assign_role(user.id, role_name)
        await db.commit()


async def _login(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _strong_password()},
    )
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.integration
async def test_signup_assigns_default_user_role(client: AsyncClient):
    data = await _signup(client)
    headers = _auth_headers(data["access_token"])

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert "user" in body["roles"]
    assert "file:upload" in body["permissions"]
    assert "user:manage" not in body["permissions"]


@pytest.mark.integration
async def test_user_can_access_user_routes_not_admin(client: AsyncClient):
    data = await _signup(client)
    headers = _auth_headers(data["access_token"])

    allowed = await client.post("/api/v1/rbac/user/execution-validation", headers=headers)
    assert allowed.status_code == 200

    denied = await client.get("/api/v1/rbac/admin/system", headers=headers)
    assert denied.status_code == 403


@pytest.mark.integration
async def test_admin_can_access_admin_routes(client: AsyncClient):
    email = _unique_email()
    data = await _signup(client, email=email)
    await _assign_role(email, "admin")
    tokens = await _login(client, email)
    headers = _auth_headers(tokens["access_token"])

    response = await client.get("/api/v1/rbac/admin/system", headers=headers)
    assert response.status_code == 200

    users = await client.get("/api/v1/rbac/admin/users", headers=headers)
    assert users.status_code == 200


@pytest.mark.integration
async def test_auditor_can_read_auditor_routes_not_manage_policies(client: AsyncClient):
    email = _unique_email()
    data = await _signup(client, email=email)
    await _assign_role(email, "auditor")
    tokens = await _login(client, email)
    headers = _auth_headers(tokens["access_token"])

    reports = await client.get("/api/v1/rbac/auditor/reports", headers=headers)
    assert reports.status_code == 200

    audit = await client.get("/api/v1/rbac/auditor/audit-logs", headers=headers)
    assert audit.status_code == 200

    blocked = await client.post(
        "/api/v1/rbac/auditor/cannot-manage-policies",
        headers=headers,
    )
    assert blocked.status_code == 403


@pytest.mark.integration
async def test_auditor_cannot_access_admin_system(client: AsyncClient):
    email = _unique_email()
    await _signup(client, email=email)
    await _assign_role(email, "auditor")
    tokens = await _login(client, email)
    headers = _auth_headers(tokens["access_token"])

    denied = await client.get("/api/v1/rbac/admin/system", headers=headers)
    assert denied.status_code == 403

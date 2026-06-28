"""Shared helpers for Sprint 2 HTTP integration tests."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.core.user_approval import APPROVAL_APPROVED
from app.db.session import AsyncSessionLocal
from app.repositories.user_repository import UserRepository
from app.services.rbac_service import RbacService

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures" / "datasets"
STRONG_PASSWORD = "SecurePass123"


def unique_email(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def skip_if_no_db(response) -> None:
    if response.status_code >= 500:
        pytest.skip("Database not available (run migrations through 016)")


async def signup_user(
    client: AsyncClient,
    *,
    email: str | None = None,
    full_name: str = "Integration Test",
) -> dict:
    email = email or unique_email()
    try:
        response = await client.post(
            "/api/v1/auth/signup",
            json={"email": email, "password": STRONG_PASSWORD, "full_name": full_name},
        )
    except OSError:
        pytest.skip("Database not available")
    skip_if_no_db(response)
    assert response.status_code == 201, response.text
    data = response.json()
    data["_email"] = email
    return data


async def approve_user(email: str, role_name: str = "user") -> None:
    async with AsyncSessionLocal() as db:
        user = await UserRepository(db).get_by_email(email)
        assert user is not None
        user.approval_status = APPROVAL_APPROVED
        user.is_active = True
        await RbacService(db).set_user_role(user.id, role_name)
        await db.commit()


async def login_user(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": STRONG_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def assign_role(email: str, role_name: str) -> None:
    await approve_user(email, role_name)


async def signup_with_role(
    client: AsyncClient, role_name: str, *, email: str | None = None
) -> dict:
    data = await signup_user(client, email=email)
    await approve_user(data["_email"], role_name)
    tokens = await login_user(client, data["_email"])
    tokens["_email"] = data["_email"]
    return tokens


async def upload_dataset(
    client: AsyncClient,
    headers: dict[str, str],
    fixture_name: str,
) -> dict:
    path = FIXTURES_DIR / fixture_name
    assert path.exists(), f"Missing fixture: {path}"
    with path.open("rb") as fh:
        response = await client.post(
            "/api/v1/files/upload",
            headers=headers,
            files={"file": (fixture_name, fh, "text/csv")},
        )
    skip_if_no_db(response)
    assert response.status_code == 201, response.text
    return response.json()["file"]


async def run_scan(
    client: AsyncClient,
    headers: dict[str, str],
    file_id: str,
) -> dict:
    response = await client.post(
        "/api/v1/scans",
        headers=headers,
        json={"file_id": file_id},
    )
    skip_if_no_db(response)
    assert response.status_code == 201, response.text
    scan = response.json()
    assert scan["status"] == "completed", scan
    return scan


async def get_seed_model(client: AsyncClient, headers: dict[str, str], code: str) -> dict:
    response = await client.get(
        "/api/v1/models",
        headers=headers,
        params={"limit": 100, "active_only": "false"},
    )
    skip_if_no_db(response)
    assert response.status_code == 200, response.text
    for item in response.json()["items"]:
        if item["code"] == code:
            return item
    pytest.fail(f"Seed model not found: {code}. Run migration 016.")

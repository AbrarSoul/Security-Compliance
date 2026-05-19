"""Tests for centralized API error response format."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_unauthorized_includes_detail(client: AsyncClient):
    response = await client.get("/api/v1/policies")
    assert response.status_code == 401
    body = response.json()
    assert "detail" in body


async def test_validation_error_includes_detail_array(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "not-valid"},
    )
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body

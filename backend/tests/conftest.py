import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("MONITORING_OUTBOX_WORKER_ENABLED", "false")

from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402

from tests.helpers.integration import STRONG_PASSWORD, unique_email  # noqa: E402


@pytest.fixture(autouse=True)
async def _dispose_db_engine_after_test():
    """Prevent asyncpg connections from leaking across pytest event loops."""
    yield
    await engine.dispose()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def strong_password() -> str:
    return STRONG_PASSWORD


@pytest.fixture
def unique_email_factory():
    return unique_email

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.audit_actions import AuditAction
from app.core import audit_severity
from app.core.request_context import RequestContext, set_request_context
from app.models.audit_log import AuditLog
from app.core.request_context import clear_request_context
from app.services.audit_service import AuditService, _sanitize_metadata


def test_sanitize_metadata_redacts_secrets():
    raw = {
        "email": "user@test.com",
        "password": "Secret123",
        "nested": {"refresh_token": "abc", "ok": True},
    }
    cleaned = _sanitize_metadata(raw)
    assert cleaned["email"] == "user@test.com"
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["nested"]["refresh_token"] == "[REDACTED]"
    assert cleaned["nested"]["ok"] is True


@pytest.mark.asyncio
async def test_audit_service_log_persists_entry():
    db = AsyncMock()
    user_id = uuid4()
    ctx = RequestContext(request_id="req-1", ip_address="127.0.0.1", user_agent="pytest")
    set_request_context(ctx)

    service = AuditService(db)
    service.repo.create = AsyncMock(side_effect=lambda entry: entry)

    entry = await service.log(
        AuditAction.AUTH_LOGIN,
        user_id=user_id,
        resource_type="user",
        resource_id=user_id,
        severity=audit_severity.INFO,
        status="success",
        metadata={"email": "a@b.com"},
    )

    assert isinstance(entry, AuditLog)
    assert entry.action == AuditAction.AUTH_LOGIN
    assert entry.user_id == user_id
    assert entry.request_id == "req-1"
    assert entry.ip_address == "127.0.0.1"
    assert entry.user_agent == "pytest"
    assert entry.metadata_json["email"] == "a@b.com"
    service.repo.create.assert_awaited_once()
    clear_request_context()


@pytest.mark.asyncio
async def test_log_execution_decision_block():
    db = AsyncMock()
    service = AuditService(db)
    service.repo.create = AsyncMock(side_effect=lambda entry: entry)
    exec_id = uuid4()
    user_id = uuid4()

    entry = await service.log_execution_decision(
        user_id,
        exec_id,
        "block",
        metadata={"reason": "policy"},
    )
    assert entry.action == AuditAction.EXECUTION_BLOCKED
    assert entry.status == "blocked"
    assert entry.severity == audit_severity.HIGH

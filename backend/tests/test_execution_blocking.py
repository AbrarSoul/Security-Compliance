"""Unit tests for execution blocking enforcement."""

import uuid
from datetime import UTC, datetime

import pytest

from app.services.execution.blocking_engine import ExecutionBlockingEngine, ExecutionBlockingError
from app.services.execution.constants import (
    STATUS_ALLOWED,
    STATUS_APPROVED_AFTER_WARNING,
    STATUS_BLOCKED,
    STATUS_STARTED,
    STATUS_WARNING_PENDING_ACK,
)
from app.services.execution.enforcement_helpers import reasons_from_summary
from app.services.execution_blocking_service import ExecutionBlockingService
from app.core.permissions import EXECUTION_READ, EXECUTION_READ_ALL, EXECUTION_REQUEST


class TestExecutionBlockingEngine:
    def setup_method(self):
        self.engine = ExecutionBlockingEngine()

    def test_status_after_validation_allow(self):
        assert self.engine.status_after_validation("allow") == STATUS_ALLOWED

    def test_status_after_validation_warn(self):
        assert self.engine.status_after_validation("warn") == STATUS_WARNING_PENDING_ACK

    def test_status_after_validation_block(self):
        assert self.engine.status_after_validation("block") == STATUS_BLOCKED

    def test_allow_can_start(self):
        self.engine.assert_can_start(status=STATUS_ALLOWED, decision="allow")

    def test_warn_cannot_start_without_ack(self):
        with pytest.raises(ExecutionBlockingError) as exc:
            self.engine.assert_can_start(
                status=STATUS_WARNING_PENDING_ACK, decision="warn"
            )
        assert exc.value.code == "acknowledgement_required"

    def test_approved_after_warning_can_start(self):
        self.engine.assert_can_start(
            status=STATUS_APPROVED_AFTER_WARNING, decision="warn"
        )

    def test_block_never_starts(self):
        with pytest.raises(ExecutionBlockingError) as exc:
            self.engine.assert_can_start(status=STATUS_BLOCKED, decision="block")
        assert exc.value.code == "execution_blocked"

    def test_already_started_conflict(self):
        with pytest.raises(ExecutionBlockingError) as exc:
            self.engine.assert_can_start(status=STATUS_STARTED, decision="allow")
        assert exc.value.code == "already_started"

    def test_acknowledge_only_when_pending(self):
        self.engine.assert_can_acknowledge(
            status=STATUS_WARNING_PENDING_ACK, decision="warn"
        )
        with pytest.raises(ExecutionBlockingError):
            self.engine.assert_can_acknowledge(status=STATUS_ALLOWED, decision="allow")

    def test_enforcement_state_allowed(self):
        state = self.engine.build_enforcement_state(
            execution_id=str(uuid.uuid4()),
            status=STATUS_ALLOWED,
            decision="allow",
            blocking_reasons=[],
            warning_reasons=[],
            recommendations=[],
            explanation="OK",
        )
        assert state.can_start is True
        assert state.requires_acknowledgement is False

    def test_enforcement_state_warn_pending(self):
        state = self.engine.build_enforcement_state(
            execution_id=str(uuid.uuid4()),
            status=STATUS_WARNING_PENDING_ACK,
            decision="warn",
            blocking_reasons=[],
            warning_reasons=["Sensitive data detected"],
            recommendations=["Anonymize dataset"],
            explanation="Caution",
        )
        assert state.can_start is False
        assert state.requires_acknowledgement is True


class TestReasonsFromSummary:
    def test_block_reasons_extracted(self):
        blocking, warning, recs = reasons_from_summary(
            {
                "decision": "block",
                "explanation": "Blocked by policy",
                "triggered_rules": [
                    {"action": "block", "reason": "Password detected"}
                ],
                "recommendations": ["Remove passwords"],
            }
        )
        assert "Blocked by policy" in blocking
        assert "Password detected" in blocking
        assert warning == []
        assert recs == ["Remove passwords"]


class TestAuditorPermissions:
    def test_auditor_is_readonly(self):
        perms = frozenset({EXECUTION_READ})
        assert ExecutionBlockingService.is_auditor_readonly(perms) is True

    def test_user_is_not_readonly(self):
        perms = frozenset({EXECUTION_REQUEST, EXECUTION_READ})
        assert ExecutionBlockingService.is_auditor_readonly(perms) is False

    def test_admin_can_start_any(self):
        perms = frozenset({EXECUTION_READ_ALL, EXECUTION_REQUEST})
        assert ExecutionBlockingService.can_start_any(perms) is True

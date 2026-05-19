"""Pure enforcement logic for execution start and acknowledgement."""

from dataclasses import dataclass
from typing import Any

from app.services.execution.constants import (
    STARTABLE_STATUSES,
    STATUS_ALLOWED,
    STATUS_APPROVED_AFTER_WARNING,
    STATUS_BLOCKED,
    STATUS_INTERRUPTED,
    STATUS_STARTED,
    STATUS_WARNING_PENDING_ACK,
)


class ExecutionBlockingError(Exception):
    def __init__(self, code: str, message: str, *, http_status: int = 400):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


@dataclass
class ExecutionEnforcementState:
    execution_id: str
    status: str
    decision: str | None
    can_start: bool
    requires_acknowledgement: bool
    blocking_reasons: list[str]
    warning_reasons: list[str]
    recommendations: list[str]
    explanation: str | None
    acknowledged_at: str | None = None
    acknowledged_by: str | None = None
    started_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "decision": self.decision,
            "can_start": self.can_start,
            "requires_acknowledgement": self.requires_acknowledgement,
            "blocking_reasons": self.blocking_reasons,
            "warning_reasons": self.warning_reasons,
            "recommendations": self.recommendations,
            "explanation": self.explanation,
            "acknowledged_at": self.acknowledged_at,
            "acknowledged_by": self.acknowledged_by,
            "started_at": self.started_at,
        }


class ExecutionBlockingEngine:
    """Enforce allow / warn / block before execution may start."""

    def assert_can_start(self, *, status: str, decision: str | None) -> None:
        if status == STATUS_BLOCKED or decision == "block":
            raise ExecutionBlockingError(
                "execution_blocked",
                "Execution is blocked and cannot be started",
                http_status=403,
            )
        if status == STATUS_WARNING_PENDING_ACK:
            raise ExecutionBlockingError(
                "acknowledgement_required",
                "Warning must be acknowledged before execution can start",
                http_status=403,
            )
        if status == STATUS_STARTED:
            raise ExecutionBlockingError(
                "already_started",
                "Execution has already been started",
                http_status=409,
            )
        if status not in STARTABLE_STATUSES:
            raise ExecutionBlockingError(
                "cannot_start",
                f"Execution cannot be started in status '{status}'",
                http_status=400,
            )

    def assert_can_continue(self, *, status: str) -> None:
        """Runtime guard: block continued processing on interrupted/blocked executions."""
        if status == STATUS_INTERRUPTED:
            raise ExecutionBlockingError(
                "execution_interrupted",
                "Execution was interrupted by the compliance guard",
                http_status=403,
            )
        if status == STATUS_BLOCKED:
            raise ExecutionBlockingError(
                "execution_blocked",
                "Execution is blocked",
                http_status=403,
            )

    def status_after_guard_block(self, *, was_started: bool) -> str:
        return STATUS_INTERRUPTED if was_started else STATUS_BLOCKED

    def assert_can_acknowledge(self, *, status: str, decision: str | None) -> None:
        if status != STATUS_WARNING_PENDING_ACK and decision != "warn":
            raise ExecutionBlockingError(
                "not_pending_warning",
                "Execution does not have a pending warning to acknowledge",
                http_status=400,
            )

    def status_after_validation(self, decision: str) -> str:
        if decision == "allow":
            return STATUS_ALLOWED
        if decision == "warn":
            return STATUS_WARNING_PENDING_ACK
        return STATUS_BLOCKED

    def build_enforcement_state(
        self,
        *,
        execution_id: str,
        status: str,
        decision: str | None,
        blocking_reasons: list[str] | None,
        warning_reasons: list[str] | None,
        recommendations: list[str] | None,
        explanation: str | None,
        acknowledged_at: str | None = None,
        acknowledged_by: str | None = None,
        started_at: str | None = None,
    ) -> ExecutionEnforcementState:
        requires_ack = status == STATUS_WARNING_PENDING_ACK
        can_start = status in STARTABLE_STATUSES and status != STATUS_BLOCKED
        return ExecutionEnforcementState(
            execution_id=execution_id,
            status=status,
            decision=decision,
            can_start=can_start and not requires_ack,
            requires_acknowledgement=requires_ack,
            blocking_reasons=blocking_reasons or [],
            warning_reasons=warning_reasons or [],
            recommendations=recommendations or [],
            explanation=explanation,
            acknowledged_at=acknowledged_at,
            acknowledged_by=acknowledged_by,
            started_at=started_at,
        )

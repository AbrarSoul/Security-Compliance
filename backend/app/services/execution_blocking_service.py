from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import EXECUTION_READ, EXECUTION_READ_ALL, EXECUTION_REQUEST
from app.models.execution_request import ExecutionRequest
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.executions import (
    AcknowledgeWarningRequest,
    AcknowledgeWarningResponse,
    ExecutionStatusResponse,
    StartExecutionResponse,
)
from app.services.audit_service import AuditService
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.execution.blocking_engine import ExecutionBlockingEngine, ExecutionBlockingError
from app.services.execution.constants import (
    STATUS_APPROVED_AFTER_WARNING,
    STATUS_INTERRUPTED,
    STATUS_STARTED,
    STATUS_WARNING_PENDING_ACK,
)


class ExecutionBlockingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executions = ExecutionRepository(db)
        self.engine = ExecutionBlockingEngine()
        self.audit = AuditService(db)
        self.monitoring = MonitoringService(db)

    async def get_status(
        self,
        execution_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> ExecutionStatusResponse:
        request = await self._get_request_for_access(
            execution_id, user_id=user_id, can_read_all=can_read_all
        )
        return self._to_status_response(request)

    async def start_execution(
        self,
        execution_id: UUID,
        *,
        user_id: UUID,
        can_start_any: bool,
        is_auditor_readonly: bool,
    ) -> StartExecutionResponse:
        if is_auditor_readonly:
            await self._audit_unauthorized_start(user_id, execution_id, reason="auditor_readonly")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auditors cannot start executions",
            )

        request = await self._get_request_for_start(
            execution_id, user_id=user_id, can_start_any=can_start_any
        )
        result = request.execution_result
        decision = result.decision if result else None

        await self.audit.log_execution_start_requested(
            user_id,
            request.id,
            metadata={"status": request.status, "decision": decision},
        )

        try:
            self.engine.assert_can_start(status=request.status, decision=decision)
        except ExecutionBlockingError as exc:
            if exc.code == "execution_blocked":
                await self.audit.log_execution_blocked(
                    user_id, request.id, metadata={"reason": exc.message}
                )
                await self.monitoring.record_execution_blocked(
                    user_id=user_id,
                    execution_request_id=request.id,
                    reason=exc.message,
                )
            raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc

        now = datetime.now(UTC)
        request.status = STATUS_STARTED
        request.started_at = now
        if result:
            result.status = "started"
        await self.executions.update_request(request)

        await self.audit.log_execution_started(
            user_id,
            request.id,
            metadata={"decision": decision, "started_at": now.isoformat()},
        )
        await self.monitoring.get_or_open_session_for_execution(
            user_id=user_id,
            execution_request_id=request.id,
        )
        await self.monitoring.record_execution_started(
            user_id=user_id,
            execution_request_id=request.id,
        )

        return StartExecutionResponse(
            execution_request_id=request.id,
            status=request.status,
            decision=decision or "allow",
            message="Execution is approved to proceed (no experiment runner invoked)",
            started_at=now,
        )

    async def acknowledge_warning(
        self,
        execution_id: UUID,
        body: AcknowledgeWarningRequest,
        *,
        user_id: UUID,
        can_ack_any: bool,
        is_auditor_readonly: bool,
    ) -> AcknowledgeWarningResponse:
        if is_auditor_readonly:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Auditors cannot acknowledge execution warnings",
            )

        request = await self._get_request_for_start(
            execution_id, user_id=user_id, can_start_any=can_ack_any
        )
        result = request.execution_result

        try:
            self.engine.assert_can_acknowledge(
                status=request.status,
                decision=result.decision if result else None,
            )
        except ExecutionBlockingError as exc:
            raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc

        now = datetime.now(UTC)
        request.status = STATUS_APPROVED_AFTER_WARNING
        request.acknowledged_at = now
        request.acknowledged_by_user_id = user_id
        if result:
            result.acknowledged_at = now
            result.acknowledged_by_user_id = user_id
            result.status = STATUS_APPROVED_AFTER_WARNING
        await self.executions.update_request(request)

        await self.audit.log_execution_warning_acknowledged(
            user_id,
            request.id,
            metadata={
                "acknowledgement_note": body.acknowledgement_note,
                "warning_reasons": result.warning_reasons_json if result else [],
            },
        )

        return AcknowledgeWarningResponse(
            execution_request_id=request.id,
            status=request.status,
            decision=result.decision if result else "warn",
            acknowledged_at=now,
            acknowledged_by_user_id=user_id,
            message="Warning acknowledged; you may now start the execution",
            can_start=True,
        )

    async def interrupt_execution(
        self,
        execution_id: UUID,
        *,
        user_id: UUID,
        reasons: list[str],
        source: str,
        decision: str = "block",
    ) -> ExecutionRequest:
        """Terminate or block an execution flow after a runtime guard violation."""
        request = await self.executions.get_request_by_id(execution_id)
        if request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution request not found",
            )

        was_started = request.status == STATUS_STARTED
        new_status = self.engine.status_after_guard_block(was_started=was_started)
        request.status = new_status

        result = request.execution_result
        if result:
            result.decision = decision
            existing_block = list(result.blocking_reasons_json or [])
            for reason in reasons:
                if reason not in existing_block:
                    existing_block.append(reason)
            result.blocking_reasons_json = existing_block
            result.status = "interrupted" if new_status == STATUS_INTERRUPTED else "blocked"
            guard_meta = dict(result.evaluation_summary_json or {})
            guard_meta["guard_interrupt"] = {
                "source": source,
                "reasons": reasons,
                "status": new_status,
            }
            result.evaluation_summary_json = guard_meta

        await self.executions.update_request(request)

        await self.audit.log_execution_blocked(
            user_id,
            request.id,
            metadata={"reasons": reasons, "source": source, "status": new_status},
        )
        await self.monitoring.record_execution_blocked(
            user_id=user_id,
            execution_request_id=request.id,
            reason="; ".join(reasons[:3]),
        )
        return request

    async def _get_request_for_access(
        self,
        execution_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> ExecutionRequest:
        if can_read_all:
            request = await self.executions.get_request_by_id(execution_id)
        else:
            request = await self.executions.get_request_for_user(execution_id, user_id)
        if request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution request not found",
            )
        return request

    async def _get_request_for_start(
        self,
        execution_id: UUID,
        *,
        user_id: UUID,
        can_start_any: bool,
    ) -> ExecutionRequest:
        if can_start_any:
            request = await self.executions.get_request_by_id(execution_id)
        else:
            request = await self.executions.get_request_for_user(execution_id, user_id)

        if request is None:
            await self._audit_unauthorized_start(
                user_id, execution_id, reason="not_found_or_not_owner"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution request not found",
            )
        return request

    async def _audit_unauthorized_start(
        self, user_id: UUID, execution_id: UUID, *, reason: str
    ) -> None:
        await self.audit.log_execution_start_unauthorized(
            user_id,
            execution_id,
            metadata={"reason": reason},
        )

    def _to_status_response(self, request: ExecutionRequest) -> ExecutionStatusResponse:
        result = request.execution_result
        eval_summary = (result.evaluation_summary_json or {}) if result else {}
        state = self.engine.build_enforcement_state(
            execution_id=str(request.id),
            status=request.status,
            decision=result.decision if result else None,
            blocking_reasons=result.blocking_reasons_json if result else [],
            warning_reasons=result.warning_reasons_json if result else [],
            recommendations=(
                result.recommendations_json
                if result and result.recommendations_json
                else eval_summary.get("recommendations", [])
            ),
            explanation=eval_summary.get("explanation"),
            acknowledged_at=(
                request.acknowledged_at.isoformat() if request.acknowledged_at else None
            ),
            acknowledged_by=(
                str(request.acknowledged_by_user_id)
                if request.acknowledged_by_user_id
                else None
            ),
            started_at=request.started_at.isoformat() if request.started_at else None,
        )
        return ExecutionStatusResponse(
            execution_request_id=request.id,
            status=state.status,
            decision=state.decision,
            risk_score=result.risk_score if result else None,
            risk_level=result.risk_level if result else None,
            can_start=state.can_start,
            requires_acknowledgement=state.requires_acknowledgement,
            blocking_reasons=state.blocking_reasons,
            warning_reasons=state.warning_reasons,
            recommendations=state.recommendations,
            explanation=state.explanation,
            acknowledged_at=request.acknowledged_at,
            acknowledged_by_user_id=request.acknowledged_by_user_id,
            started_at=request.started_at,
        )

    @staticmethod
    def is_auditor_readonly(ctx_permissions: frozenset[str]) -> bool:
        """Auditor has execution:read but not execution:request."""
        return EXECUTION_READ in ctx_permissions and EXECUTION_REQUEST not in ctx_permissions

    @staticmethod
    def can_read_all(ctx_permissions: frozenset[str]) -> bool:
        return EXECUTION_READ_ALL in ctx_permissions or EXECUTION_READ in ctx_permissions

    @staticmethod
    def can_start_any(ctx_permissions: frozenset[str]) -> bool:
        return EXECUTION_READ_ALL in ctx_permissions

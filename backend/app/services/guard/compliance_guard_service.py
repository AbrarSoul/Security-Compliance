"""Real-time compliance guard — orchestrates scans, policies, and execution control."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guard_enforcement_log import GuardEnforcementLog
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.guard_repository import GuardRepository
from app.services.audit_service import AuditService
from app.services.events.constants import (
    EXECUTION_INTERRUPTED,
    GUARD_ENFORCED,
    GUARD_OUTPUT_BLOCKED,
    GUARD_PROMPT_BLOCKED,
    GUARD_WARNING,
    POLICY_VIOLATION,
    RULE_TRIGGERED,
)
from app.services.events.dispatcher import EventDispatcher
from app.services.events.types import DomainEventEnvelope
from app.services.execution.blocking_engine import ExecutionBlockingEngine, ExecutionBlockingError
from app.services.execution.constants import STATUS_INTERRUPTED
from app.services.prompts.constants import DECISION_BLOCK, DECISION_WARN
from app.services.execution_blocking_service import ExecutionBlockingService
from app.services.guard.constants import (
    ACTION_ALLOWED,
    ACTION_BLOCKED,
    ACTION_INTERRUPTED,
    ACTION_WARNED,
    ENFORCEMENT_OUTPUT_GUARD,
    ENFORCEMENT_PROMPT_GUARD,
    GUARD_SOURCE_COMBINED,
    GUARD_SOURCE_OUTPUT,
    GUARD_SOURCE_PROMPT,
)
from app.services.guard.runtime_enforcement_engine import RuntimeEnforcementEngine
from app.services.guard.runtime_policy_enforcer import RuntimePolicyEnforcer
from app.services.guard.types import GuardResult
from app.services.monitoring.monitoring_service import MonitoringService
from app.services.outputs.output_compliance_service import OutputComplianceService
from app.services.prompts.prompt_monitoring_service import PromptMonitoringService


class ComplianceGuardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executions = ExecutionRepository(db)
        self.guard_repo = GuardRepository(db)
        self.prompt_monitoring = PromptMonitoringService(db)
        self.output_compliance = OutputComplianceService(db)
        self.runtime_policy = RuntimePolicyEnforcer(db)
        self.enforcement = RuntimeEnforcementEngine()
        self.blocking = ExecutionBlockingService(db)
        self.blocking_engine = ExecutionBlockingEngine()
        self.monitoring = MonitoringService(db)
        self.dispatcher = EventDispatcher(db)
        self.audit = AuditService(db)

    async def guard_prompt(
        self,
        execution_request_id: UUID,
        *,
        user_id: UUID,
        prompt: str,
        can_access_any: bool = False,
        metadata: dict | None = None,
    ) -> GuardResult:
        request = await self._load_execution(
            execution_request_id, user_id=user_id, can_access_any=can_access_any
        )
        self._assert_can_process(request)

        prompt_scan, scan_outcome = await self.prompt_monitoring.scan_prompt(
            user_id=user_id,
            prompt=prompt,
            execution_request_id=execution_request_id,
            metadata=metadata,
            can_read_all_sessions=can_access_any,
        )
        session_id = prompt_scan.session_id

        finding_types = [f.finding_type for f in scan_outcome.findings]
        rule_result, policy_result, _ = await self.runtime_policy.evaluate(
            execution_request_id,
            runtime_finding_types=finding_types,
            runtime_risk_score=scan_outcome.risk_score,
        )

        rule_decision = rule_result.recommended_action
        policy_decision = self.runtime_policy.worst_policy_decision(policy_result)
        policy_reasons = [
            pr.decision_reason
            for pr in policy_result.policy_results
            if pr.recommended_action in ("block", "warn")
        ]
        rule_reasons = [t.reason for t in rule_result.triggered_rules]

        final_decision, risk_score, risk_level, blocking, warnings, recommendations = (
            self.enforcement.merge(
                scan_decision=scan_outcome.decision,
                scan_risk_score=scan_outcome.risk_score,
                scan_risk_level=scan_outcome.risk_level,
                scan_reasons=scan_outcome.blocking_reasons + scan_outcome.warning_reasons,
                scan_source=GUARD_SOURCE_PROMPT,
                rule_decision=rule_decision,
                rule_risk_score=rule_result.aggregated_risk_score,
                rule_reasons=rule_reasons,
                policy_decision=policy_decision,
                policy_risk_score=max(
                    (pr.validation_score or 0) for pr in policy_result.policy_results
                )
                if policy_result.policy_results
                else 0,
                policy_reasons=policy_reasons,
            )
        )

        interrupted = False
        action_taken = ACTION_ALLOWED
        if final_decision == DECISION_BLOCK:
            updated = await self._interrupt(request, user_id, blocking, source=GUARD_SOURCE_PROMPT)
            interrupted = updated.status == STATUS_INTERRUPTED
            request = updated
            action_taken = ACTION_INTERRUPTED if interrupted else ACTION_BLOCKED
        elif final_decision == DECISION_WARN:
            action_taken = ACTION_WARNED

        result = GuardResult(
            allowed=final_decision != DECISION_BLOCK,
            decision=final_decision,
            risk_score=risk_score,
            risk_level=risk_level,
            execution_request_id=execution_request_id,
            session_id=session_id,
            prompt_scan_id=prompt_scan.id,
            interrupted=interrupted,
            execution_status=request.status,
            blocking_reasons=blocking,
            warning_reasons=warnings,
            recommendations=recommendations,
            masked_content=scan_outcome.masked_prompt,
            scan_decision=self.enforcement.to_guard_decision(
                scan_outcome.decision,
                scan_outcome.risk_score,
                scan_outcome.risk_level,
                GUARD_SOURCE_PROMPT,
                scan_outcome.blocking_reasons + scan_outcome.warning_reasons,
            ),
            rule_decision=self.enforcement.to_guard_decision(
                rule_decision,
                rule_result.aggregated_risk_score,
                rule_result.aggregated_severity or "low",
                "runtime_rule",
                rule_reasons,
            ),
            policy_decision=self.enforcement.to_guard_decision(
                policy_decision,
                0,
                "medium",
                "runtime_policy",
                policy_reasons,
            ),
            triggered_rules=[t.to_dict() for t in rule_result.triggered_rules],
            policy_violations=self.runtime_policy.policy_violations(policy_result),
        )

        await self._finalize_guard(
            result=result,
            user_id=user_id,
            request=request,
            session_id=session_id,
            enforcement_type=ENFORCEMENT_PROMPT_GUARD,
            source=GUARD_SOURCE_PROMPT,
            action_taken=action_taken,
            prompt_scan_id=prompt_scan.id,
            rule_result=rule_result,
            policy_result=policy_result,
        )
        return result

    async def guard_output(
        self,
        execution_request_id: UUID,
        *,
        user_id: UUID,
        output_text: str,
        prompt_scan_id: UUID | None = None,
        can_access_any: bool = False,
        metadata: dict | None = None,
    ) -> GuardResult:
        request = await self._load_execution(
            execution_request_id, user_id=user_id, can_access_any=can_access_any
        )
        self._assert_can_process(request)

        output_scan, scan_outcome = await self.output_compliance.scan_output(
            user_id=user_id,
            output_text=output_text,
            execution_request_id=execution_request_id,
            prompt_scan_id=prompt_scan_id,
            metadata=metadata,
            can_read_all_sessions=can_access_any,
        )
        session_id = output_scan.session_id

        finding_types = [f.finding_type for f in scan_outcome.findings]
        rule_result, policy_result, _ = await self.runtime_policy.evaluate(
            execution_request_id,
            runtime_finding_types=finding_types,
            runtime_risk_score=scan_outcome.risk_score,
        )

        rule_decision = rule_result.recommended_action
        policy_decision = self.runtime_policy.worst_policy_decision(policy_result)
        policy_reasons = [
            pr.decision_reason
            for pr in policy_result.policy_results
            if pr.recommended_action in ("block", "warn")
        ]
        rule_reasons = [t.reason for t in rule_result.triggered_rules]

        final_decision, risk_score, risk_level, blocking, warnings, recommendations = (
            self.enforcement.merge(
                scan_decision=scan_outcome.decision,
                scan_risk_score=scan_outcome.risk_score,
                scan_risk_level=scan_outcome.risk_level,
                scan_reasons=scan_outcome.blocking_reasons + scan_outcome.warning_reasons,
                scan_source=GUARD_SOURCE_OUTPUT,
                rule_decision=rule_decision,
                rule_risk_score=rule_result.aggregated_risk_score,
                rule_reasons=rule_reasons,
                policy_decision=policy_decision,
                policy_risk_score=max(
                    (pr.validation_score or 0) for pr in policy_result.policy_results
                )
                if policy_result.policy_results
                else 0,
                policy_reasons=policy_reasons,
            )
        )

        interrupted = False
        action_taken = ACTION_ALLOWED
        if final_decision == DECISION_BLOCK:
            updated = await self._interrupt(request, user_id, blocking, source=GUARD_SOURCE_OUTPUT)
            interrupted = updated.status == STATUS_INTERRUPTED
            request = updated
            action_taken = ACTION_INTERRUPTED if interrupted else ACTION_BLOCKED
        elif final_decision == DECISION_WARN:
            action_taken = ACTION_WARNED

        result = GuardResult(
            allowed=final_decision != DECISION_BLOCK,
            decision=final_decision,
            risk_score=risk_score,
            risk_level=risk_level,
            execution_request_id=execution_request_id,
            session_id=session_id,
            output_scan_id=output_scan.id,
            prompt_scan_id=prompt_scan_id,
            interrupted=interrupted,
            execution_status=request.status,
            blocking_reasons=blocking,
            warning_reasons=warnings,
            recommendations=recommendations,
            masked_content=scan_outcome.masked_output,
            redacted_content=scan_outcome.redacted_output,
            scan_decision=self.enforcement.to_guard_decision(
                scan_outcome.decision,
                scan_outcome.risk_score,
                scan_outcome.risk_level,
                GUARD_SOURCE_OUTPUT,
                scan_outcome.blocking_reasons + scan_outcome.warning_reasons,
            ),
            rule_decision=self.enforcement.to_guard_decision(
                rule_decision,
                rule_result.aggregated_risk_score,
                rule_result.aggregated_severity or "low",
                "runtime_rule",
                rule_reasons,
            ),
            policy_decision=self.enforcement.to_guard_decision(
                policy_decision,
                0,
                "medium",
                "runtime_policy",
                policy_reasons,
            ),
            triggered_rules=[t.to_dict() for t in rule_result.triggered_rules],
            policy_violations=self.runtime_policy.policy_violations(policy_result),
        )

        await self._finalize_guard(
            result=result,
            user_id=user_id,
            request=request,
            session_id=session_id,
            enforcement_type=ENFORCEMENT_OUTPUT_GUARD,
            source=GUARD_SOURCE_OUTPUT,
            action_taken=action_taken,
            output_scan_id=output_scan.id,
            rule_result=rule_result,
            policy_result=policy_result,
        )
        return result

    async def get_guard_status(
        self,
        execution_request_id: UUID,
        *,
        user_id: UUID,
        can_access_any: bool,
    ) -> dict:
        request = await self._load_execution(
            execution_request_id, user_id=user_id, can_access_any=can_access_any
        )
        logs = await self.guard_repo.list_for_execution(execution_request_id)
        result = request.execution_result
        return {
            "execution_request_id": str(execution_request_id),
            "status": request.status,
            "decision": result.decision if result else None,
            "can_continue": request.status not in ("interrupted", "blocked"),
            "guard_actions": [
                {
                    "id": log.id,
                    "enforcement_type": log.enforcement_type,
                    "decision": log.decision,
                    "action_taken": log.action_taken,
                    "source": log.source,
                    "created_at": log.created_at,
                }
                for log in logs
            ],
        }

    async def _load_execution(self, execution_id: UUID, *, user_id: UUID, can_access_any: bool):
        if can_access_any:
            request = await self.executions.get_request_by_id(execution_id)
        else:
            request = await self.executions.get_request_for_user(execution_id, user_id)
        if request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution request not found",
            )
        return request

    def _assert_can_process(self, request) -> None:
        try:
            self.blocking_engine.assert_can_continue(status=request.status)
        except ExecutionBlockingError as exc:
            raise HTTPException(status_code=exc.http_status, detail=exc.message) from exc

    async def _interrupt(self, request, user_id: UUID, reasons: list[str], *, source: str):
        if not reasons:
            reasons = ["Compliance guard blocked this operation"]
        return await self.blocking.interrupt_execution(
            request.id,
            user_id=user_id,
            reasons=reasons,
            source=source,
        )

    async def _finalize_guard(
        self,
        *,
        result: GuardResult,
        user_id: UUID,
        request,
        session_id: UUID | None,
        enforcement_type: str,
        source: str,
        action_taken: str,
        rule_result,
        policy_result,
        prompt_scan_id: UUID | None = None,
        output_scan_id: UUID | None = None,
    ) -> None:
        await self.guard_repo.create_log(
            GuardEnforcementLog(
                execution_request_id=result.execution_request_id,
                user_id=user_id,
                session_id=session_id,
                enforcement_type=enforcement_type,
                source=GUARD_SOURCE_COMBINED,
                decision=result.decision,
                action_taken=action_taken,
                prompt_scan_id=prompt_scan_id,
                output_scan_id=output_scan_id,
                reasons_json=result.blocking_reasons + result.warning_reasons,
                metadata_json=result.to_dict(),
            )
        )

        await self.audit.log_guard_enforcement(
            user_id,
            result.execution_request_id,
            decision=result.decision,
            source=source,
            interrupted=result.interrupted,
            metadata={"action_taken": action_taken, "risk_score": result.risk_score},
        )

        payload = {
            "decision": result.decision,
            "risk_score": result.risk_score,
            "interrupted": result.interrupted,
            "source": source,
        }
        await self.dispatcher.publish(
            DomainEventEnvelope(
                event_type=GUARD_ENFORCED,
                user_id=user_id,
                session_id=session_id,
                resource_type="execution_request",
                resource_id=result.execution_request_id,
                severity="high" if result.decision == DECISION_BLOCK else "info",
                payload=payload,
            )
        )

        if result.decision == DECISION_BLOCK:
            block_event = (
                GUARD_PROMPT_BLOCKED if source == GUARD_SOURCE_PROMPT else GUARD_OUTPUT_BLOCKED
            )
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=block_event,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="execution_request",
                    resource_id=result.execution_request_id,
                    severity="high",
                    payload={**payload, "blocking_reasons": result.blocking_reasons},
                )
            )
            if result.interrupted:
                await self.dispatcher.publish(
                    DomainEventEnvelope(
                        event_type=EXECUTION_INTERRUPTED,
                        user_id=user_id,
                        session_id=session_id,
                        resource_type="execution_request",
                        resource_id=result.execution_request_id,
                        severity="critical",
                        payload=payload,
                    )
                )
        elif result.decision == DECISION_WARN:
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=GUARD_WARNING,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="execution_request",
                    resource_id=result.execution_request_id,
                    severity="warning",
                    payload={**payload, "warning_reasons": result.warning_reasons},
                )
            )

        for triggered in rule_result.triggered_rules:
            await self.monitoring.record_rule_triggered(
                user_id=user_id,
                session_id=session_id,
                rule_id=triggered.rule_id,
                rule_code=triggered.rule_code,
                metadata={"reason": triggered.reason, "guard": True},
            )
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=RULE_TRIGGERED,
                    user_id=user_id,
                    session_id=session_id,
                    resource_id=triggered.rule_id,
                    resource_type="compliance_rule",
                    severity=triggered.severity,
                    payload=triggered.to_dict(),
                )
            )

        for violation in self.runtime_policy.policy_violations(policy_result):
            await self.dispatcher.publish(
                DomainEventEnvelope(
                    event_type=POLICY_VIOLATION,
                    user_id=user_id,
                    session_id=session_id,
                    resource_type="compliance_policy",
                    resource_id=UUID(violation["policy_id"]),
                    severity="high",
                    payload=violation,
                )
            )

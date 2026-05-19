"""Real-time compliance guard APIs (Sprint 3 Step 5)."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import (
    EXECUTION_READ,
    EXECUTION_READ_ALL,
    EXECUTION_REQUEST,
    MONITORING_PUBLISH,
)
from app.db.session import get_db
from app.schemas.compliance_guard import (
    GuardActionSummary,
    GuardDecisionDetail,
    GuardOutputRequest,
    GuardPromptRequest,
    GuardResultResponse,
    GuardStatusResponse,
)
from app.services.guard.compliance_guard_service import ComplianceGuardService

router = APIRouter(prefix="/monitoring/guard", tags=["compliance-guard"])


def get_guard_service(db: AsyncSession = Depends(get_db)) -> ComplianceGuardService:
    return ComplianceGuardService(db)


def _to_response(result) -> GuardResultResponse:
    def _detail(d) -> GuardDecisionDetail | None:
        if d is None:
            return None
        return GuardDecisionDetail(
            decision=d.decision,
            risk_score=d.risk_score,
            risk_level=d.risk_level,
            source=d.source,
            reasons=d.reasons,
        )

    return GuardResultResponse(
        allowed=result.allowed,
        decision=result.decision,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        execution_request_id=result.execution_request_id,
        session_id=result.session_id,
        prompt_scan_id=result.prompt_scan_id,
        output_scan_id=result.output_scan_id,
        interrupted=result.interrupted,
        execution_status=result.execution_status,
        blocking_reasons=result.blocking_reasons,
        warning_reasons=result.warning_reasons,
        recommendations=result.recommendations,
        masked_content=result.masked_content,
        redacted_content=result.redacted_content,
        scan_decision=_detail(result.scan_decision),
        rule_decision=_detail(result.rule_decision),
        policy_decision=_detail(result.policy_decision),
        triggered_rules=result.triggered_rules,
        policy_violations=result.policy_violations,
    )


@router.post(
    "/executions/{execution_id}/prompt",
    response_model=GuardResultResponse,
    status_code=status.HTTP_200_OK,
)
async def guard_prompt(
    execution_id: UUID,
    body: GuardPromptRequest,
    auth: AuthContext = Depends(require_permission(MONITORING_PUBLISH)),
    service: ComplianceGuardService = Depends(get_guard_service),
):
    can_any = auth.has_permission(EXECUTION_READ_ALL)
    result = await service.guard_prompt(
        execution_id,
        user_id=auth.user.id,
        prompt=body.prompt,
        can_access_any=can_any,
        metadata=body.metadata,
    )
    return _to_response(result)


@router.post(
    "/executions/{execution_id}/output",
    response_model=GuardResultResponse,
    status_code=status.HTTP_200_OK,
)
async def guard_output(
    execution_id: UUID,
    body: GuardOutputRequest,
    auth: AuthContext = Depends(require_permission(MONITORING_PUBLISH)),
    service: ComplianceGuardService = Depends(get_guard_service),
):
    can_any = auth.has_permission(EXECUTION_READ_ALL)
    result = await service.guard_output(
        execution_id,
        user_id=auth.user.id,
        output_text=body.output,
        prompt_scan_id=body.prompt_scan_id,
        can_access_any=can_any,
        metadata=body.metadata,
    )
    return _to_response(result)


@router.get("/executions/{execution_id}/status", response_model=GuardStatusResponse)
async def guard_status(
    execution_id: UUID,
    auth: AuthContext = Depends(
        require_any_permission(EXECUTION_READ, EXECUTION_READ_ALL, EXECUTION_REQUEST)
    ),
    service: ComplianceGuardService = Depends(get_guard_service),
):
    can_any = auth.has_permission(EXECUTION_READ_ALL)
    data = await service.get_guard_status(
        execution_id,
        user_id=auth.user.id,
        can_access_any=can_any,
    )
    actions = [
        GuardActionSummary(
            id=a["id"] if isinstance(a["id"], UUID) else UUID(str(a["id"])),
            enforcement_type=a["enforcement_type"],
            decision=a["decision"],
            action_taken=a["action_taken"],
            source=a["source"],
            created_at=a["created_at"]
            if hasattr(a["created_at"], "isoformat")
            else a["created_at"],
        )
        for a in data["guard_actions"]
    ]
    return GuardStatusResponse(
        execution_request_id=execution_id,
        status=data["status"],
        decision=data["decision"],
        can_continue=data["can_continue"],
        guard_actions=actions,
    )

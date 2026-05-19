"""Real-time prompt monitoring APIs (Sprint 3 Step 3)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import MONITORING_PUBLISH, MONITORING_READ, MONITORING_READ_ALL
from app.db.session import get_db
from app.schemas.prompt_monitoring import (
    PromptFindingResponse,
    PromptScanDetailResponse,
    PromptScanListResponse,
    ScanPromptRequest,
    ScanPromptResponse,
)
from app.services.prompts.constants import DECISION_BLOCK
from app.services.prompts.prompt_monitoring_service import PromptMonitoringService

router = APIRouter(prefix="/monitoring/prompts", tags=["prompt-monitoring"])


def get_prompt_service(db: AsyncSession = Depends(get_db)) -> PromptMonitoringService:
    return PromptMonitoringService(db)


def _findings_from_json(raw: list | None) -> list[PromptFindingResponse]:
    if not raw:
        return []
    return [PromptFindingResponse.model_validate(item) for item in raw]


def _scan_to_detail(scan) -> PromptScanDetailResponse:
    return PromptScanDetailResponse(
        id=scan.id,
        user_id=scan.user_id,
        session_id=scan.session_id,
        execution_request_id=scan.execution_request_id,
        prompt_hash=scan.prompt_hash,
        content_length=scan.content_length,
        decision=scan.decision,
        risk_score=scan.risk_score,
        risk_level=scan.risk_level,
        findings=_findings_from_json(scan.findings_json),
        masked_prompt=scan.masked_prompt,
        blocking_reasons=scan.blocking_reasons_json or [],
        warning_reasons=scan.warning_reasons_json or [],
        recommendations=scan.recommendations_json or [],
        metadata_json=scan.metadata_json,
        scanned_at=scan.scanned_at,
        can_proceed=scan.decision != DECISION_BLOCK,
    )


@router.post("/scan", response_model=ScanPromptResponse, status_code=status.HTTP_201_CREATED)
async def scan_prompt(
    body: ScanPromptRequest,
    auth: AuthContext = Depends(require_permission(MONITORING_PUBLISH)),
    service: PromptMonitoringService = Depends(get_prompt_service),
):
    can_read_all = auth.has_permission(MONITORING_READ_ALL)
    scan, outcome = await service.scan_prompt(
        user_id=auth.user.id,
        prompt=body.prompt,
        session_id=body.session_id,
        execution_request_id=body.execution_request_id,
        metadata=body.metadata,
        can_read_all_sessions=can_read_all,
    )
    return ScanPromptResponse(
        scan_id=scan.id,
        decision=outcome.decision,
        risk_score=outcome.risk_score,
        risk_level=outcome.risk_level,
        can_proceed=outcome.can_proceed,
        findings=[PromptFindingResponse.model_validate(f.to_dict()) for f in outcome.findings],
        masked_prompt=outcome.masked_prompt,
        blocking_reasons=outcome.blocking_reasons,
        warning_reasons=outcome.warning_reasons,
        recommendations=outcome.recommendations,
        prompt_hash=scan.prompt_hash,
        session_id=scan.session_id,
    )


@router.get("/scans/{scan_id}", response_model=PromptScanDetailResponse)
async def get_prompt_scan(
    scan_id: UUID,
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: PromptMonitoringService = Depends(get_prompt_service),
):
    scan = await service.get_scan(
        scan_id,
        user_id=auth.user.id,
        can_read_all=auth.has_permission(MONITORING_READ_ALL),
    )
    return _scan_to_detail(scan)


@router.get("/scans", response_model=PromptScanListResponse)
async def list_prompt_scans(
    session_id: UUID | None = Query(default=None),
    decision: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(MONITORING_READ, MONITORING_READ_ALL)),
    service: PromptMonitoringService = Depends(get_prompt_service),
):
    can_read_all = auth.has_permission(MONITORING_READ_ALL)
    scans, total = await service.list_scans(
        user_id=auth.user.id,
        can_read_all=can_read_all,
        session_id=session_id,
        decision=decision,
        limit=limit,
        offset=offset,
    )
    return PromptScanListResponse(
        items=[_scan_to_detail(s) for s in scans],
        total=total,
        limit=limit,
        offset=offset,
    )

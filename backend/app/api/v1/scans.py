from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import SCAN_READ, SCAN_RUN
from app.db.session import get_db
from app.schemas.scans import (
    CreateScanRequest,
    ScanDetailResponse,
    ScanFindingResponse,
    ScanListResponse,
    ScanSummaryResponse,
)
from app.schemas.recommendations import RecommendationListResponse, RecommendationResponse
from app.schemas.rules import RuleEvaluationResponse
from app.schemas.scoring import ComplianceScoreResponse
from app.services.scan_service import ScanService
from app.storage import get_storage_backend

router = APIRouter(prefix="/scans", tags=["compliance-scans"])


def get_scan_service(db: AsyncSession = Depends(get_db)) -> ScanService:
    return ScanService(db, get_storage_backend())


def _to_compliance_score(scan) -> ComplianceScoreResponse | None:
    if scan.status != "completed" or not scan.score_breakdown_json:
        return None
    return ComplianceScoreResponse.model_validate(scan.score_breakdown_json)


def _to_rule_evaluation(scan) -> RuleEvaluationResponse | None:
    if scan.status != "completed" or not scan.rule_evaluation_json:
        return None
    return RuleEvaluationResponse.model_validate(scan.rule_evaluation_json)


def _to_recommendations(scan) -> list[RecommendationResponse]:
    if not scan.recommendations:
        return []
    return [RecommendationResponse.model_validate(r) for r in scan.recommendations]


def _to_detail(scan) -> ScanDetailResponse:
    return ScanDetailResponse(
        **_to_summary(scan).model_dump(),
        findings=[ScanFindingResponse.model_validate(f) for f in scan.findings],
        recommendations=_to_recommendations(scan),
        compliance_score=_to_compliance_score(scan),
        rule_evaluation=_to_rule_evaluation(scan),
    )


def _to_summary(scan, include_findings_count: bool = True) -> ScanSummaryResponse:
    return ScanSummaryResponse(
        id=scan.id,
        file_id=scan.file_id,
        status=scan.status,
        risk_score=scan.risk_score,
        compliance_status=scan.compliance_status,
        classification=scan.classification,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
        findings_count=len(scan.findings) if include_findings_count and scan.findings else 0,
    )


@router.post("", response_model=ScanDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    body: CreateScanRequest,
    ctx: AuthContext = Depends(require_permission(SCAN_RUN)),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Run a compliance scan on an uploaded dataset."""
    scan = await scan_service.create_and_run_scan(ctx.user.id, body.file_id)
    return _to_detail(scan)


@router.get("", response_model=ScanListResponse)
async def list_scans(
    ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    scan_service: ScanService = Depends(get_scan_service),
):
    """List compliance scans for the authenticated user."""
    items = await scan_service.list_scans(ctx.user.id, limit=limit, offset=offset)
    return ScanListResponse(
        items=[_to_summary(s) for s in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{scan_id}", response_model=ScanDetailResponse)
async def get_scan(
    scan_id: UUID,
    ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Get scan results including detected issues and recommendations."""
    scan = await scan_service.get_scan(scan_id, ctx.user.id)
    return _to_detail(scan)


@router.get("/{scan_id}/recommendations", response_model=RecommendationListResponse)
async def get_scan_recommendations(
    scan_id: UUID,
    ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    scan_service: ScanService = Depends(get_scan_service),
):
    """Get actionable recommendations for a completed scan."""
    scan = await scan_service.get_scan(scan_id, ctx.user.id)
    items = _to_recommendations(scan)
    return RecommendationListResponse(items=items, total=len(items))

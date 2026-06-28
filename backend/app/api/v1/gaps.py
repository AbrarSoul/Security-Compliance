"""Compliance gap analysis APIs (Sprint 3 Step 8)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import GAP_ANALYZE, GAP_READ, GAP_READ_ALL
from app.db.session import get_db
from app.schemas.gaps import (
    ComplianceGapResponse,
    GapAnalysisRunDetailResponse,
    GapAnalysisRunResponse,
    GapDashboardResponse,
    GapListResponse,
    GapRunListResponse,
)
from app.services.compliance.framework_mappings import aggregate_by_framework
from app.services.gaps.gap_service import GapAnalysisService
from app.services.gaps.response_helpers import gap_to_response

router = APIRouter(prefix="/gaps", tags=["compliance-gaps"])


def get_gap_service(db: AsyncSession = Depends(get_db)) -> GapAnalysisService:
    return GapAnalysisService(db)


@router.post("/analyze", response_model=GapAnalysisRunDetailResponse, status_code=status.HTTP_201_CREATED)
async def run_gap_analysis(
    auth: AuthContext = Depends(require_permission(GAP_ANALYZE)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    """Run full compliance gap analysis and persist findings."""
    run = await service.run_analysis(triggered_by_user_id=auth.user.id)
    run = await service.get_run(run.id)
    posture = (run.summary_json or {}).get("posture_score") if run else None
    return GapAnalysisRunDetailResponse(
        **GapAnalysisRunResponse.model_validate(run).model_dump(),
        gaps=[gap_to_response(g) for g in (run.gaps if run else [])],
        posture_score=posture,
    )


@router.get("/dashboard", response_model=GapDashboardResponse)
async def gap_dashboard(
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    """Summary for gap analysis dashboard."""
    run = await service.get_latest()
    if run is None:
        return GapDashboardResponse(
            latest_run=None,
            open_gaps=[],
            open_total=0,
            by_severity={},
            by_category={},
            by_framework={},
            posture_score=100,
            last_analyzed_at=None,
        )

    gaps, total, _ = await service.list_current_gaps(status="open", limit=50)
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for g in gaps:
        by_severity[g.severity] = by_severity.get(g.severity, 0) + 1
        by_category[g.category] = by_category.get(g.category, 0) + 1

    return GapDashboardResponse(
        latest_run=GapAnalysisRunResponse.model_validate(run),
        open_gaps=[gap_to_response(g) for g in gaps],
        open_total=total,
        by_severity=by_severity,
        by_category=by_category,
        by_framework=aggregate_by_framework(gaps),
        posture_score=(run.summary_json or {}).get("posture_score", 100),
        last_analyzed_at=run.completed_at or run.started_at,
    )


@router.get("", response_model=GapListResponse)
async def list_gaps(
    severity: str | None = Query(default=None),
    gap_type: str | None = Query(default=None),
    status: str | None = Query(default="open"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    gaps, total, run = await service.list_current_gaps(
        severity=severity, gap_type=gap_type, status=status, limit=limit, offset=offset
    )
    posture = (run.summary_json or {}).get("posture_score") if run else None
    return GapListResponse(
        items=[gap_to_response(g) for g in gaps],
        total=total,
        limit=limit,
        offset=offset,
        latest_run_id=run.id if run else None,
        posture_score=posture,
    )


@router.get("/history", response_model=GapListResponse)
async def gap_history(
    gap_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    items, total = await service.list_history(
        gap_type=gap_type, severity=severity, limit=limit, offset=offset
    )
    return GapListResponse(
        items=[gap_to_response(g) for g in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/runs", response_model=GapRunListResponse)
async def list_analysis_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    items, total = await service.list_runs(limit=limit, offset=offset)
    return GapRunListResponse(
        items=[GapAnalysisRunResponse.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/{run_id}", response_model=GapAnalysisRunDetailResponse)
async def get_analysis_run(
    run_id: UUID,
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    run = await service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")
    posture = (run.summary_json or {}).get("posture_score")
    return GapAnalysisRunDetailResponse(
        **GapAnalysisRunResponse.model_validate(run).model_dump(),
        gaps=[gap_to_response(g) for g in run.gaps],
        posture_score=posture,
    )


@router.get("/{gap_id}", response_model=ComplianceGapResponse)
async def get_gap(
    gap_id: UUID,
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    gap = await service.get_gap(gap_id)
    if gap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gap not found")
    return gap_to_response(gap)


@router.post("/{gap_id}/acknowledge", response_model=ComplianceGapResponse)
async def acknowledge_gap(
    gap_id: UUID,
    auth: AuthContext = Depends(require_permission(GAP_ANALYZE)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    try:
        gap = await service.acknowledge_gap(gap_id, auth.user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gap not found") from None
    return gap_to_response(gap)


@router.post("/{gap_id}/resolve", response_model=ComplianceGapResponse)
async def resolve_gap(
    gap_id: UUID,
    auth: AuthContext = Depends(require_permission(GAP_ANALYZE)),
    service: GapAnalysisService = Depends(get_gap_service),
):
    try:
        gap = await service.resolve_gap(gap_id, auth.user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gap not found") from None
    return gap_to_response(gap)

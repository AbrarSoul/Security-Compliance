from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import REPORT_READ, REPORT_READ_ALL, SCAN_RUN
from app.db.session import get_db
from app.schemas.reports import (
    CreateReportRequest,
    ReportDetailResponse,
    ReportGenerateResponse,
    ReportListResponse,
    ReportSummaryResponse,
)
from app.services.reports.report_service import ReportService
from app.storage import get_storage_backend

router = APIRouter(prefix="/reports", tags=["compliance-reports"])


def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db, get_storage_backend())


def _to_summary(report) -> ReportSummaryResponse:
    summary = report.summary_json or {}
    return ReportSummaryResponse(
        id=report.id,
        scan_id=report.scan_id,
        created_at=report.created_at,
        executive_summary=summary.get("executive_summary", {}),
    )


def _can_read_all_reports(ctx: AuthContext) -> bool:
    return REPORT_READ_ALL in ctx.permissions


@router.post("", response_model=ReportGenerateResponse, status_code=201)
async def generate_report(
    body: CreateReportRequest,
    ctx: AuthContext = Depends(require_permission(SCAN_RUN)),
    report_service: ReportService = Depends(get_report_service),
):
    """Generate JSON and PDF compliance reports for a completed scan."""
    report = await report_service.generate_report(ctx.user.id, body.scan_id)
    return ReportGenerateResponse(report=ReportDetailResponse.from_report(report))


@router.get("", response_model=ReportListResponse)
async def list_reports(
    ctx: AuthContext = Depends(require_any_permission(REPORT_READ, REPORT_READ_ALL)),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    report_service: ReportService = Depends(get_report_service),
):
    """List reports (own files for users; all reports for admin/auditor)."""
    items = await report_service.list_reports(
        ctx.user.id,
        can_read_all=_can_read_all_reports(ctx),
        limit=limit,
        offset=offset,
    )
    return ReportListResponse(
        items=[_to_summary(r) for r in items],
        total=len(items),
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: UUID,
    ctx: AuthContext = Depends(require_any_permission(REPORT_READ, REPORT_READ_ALL)),
    report_service: ReportService = Depends(get_report_service),
):
    """Get report metadata and full JSON summary."""
    report = await report_service.get_report(
        report_id,
        ctx.user.id,
        can_read_all=_can_read_all_reports(ctx),
    )
    return ReportDetailResponse.from_report(report)


@router.get("/{report_id}/export")
async def export_report(
    report_id: UUID,
    ctx: AuthContext = Depends(require_any_permission(REPORT_READ, REPORT_READ_ALL)),
    format: str = Query(default="json", alias="format", pattern="^(json|pdf)$"),
    report_service: ReportService = Depends(get_report_service),
):
    """Download report as JSON or PDF."""
    can_read_all = _can_read_all_reports(ctx)
    content, filename, media_type = await report_service.export_report(
        report_id,
        ctx.user.id,
        format,
        can_read_all=can_read_all,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

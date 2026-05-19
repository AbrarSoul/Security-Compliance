"""Security monitoring and threat detection APIs (Sprint 3 Step 9)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import THREAT_MANAGE, THREAT_READ, THREAT_READ_ALL
from app.db.session import get_db
from app.repositories.threat_repository import ThreatRepository
from app.schemas.threats import (
    SecurityEventListResponse,
    SecurityEventLogResponse,
    SecurityThreatResponse,
    ThreatDashboardResponse,
    ThreatDetectionRunResponse,
    ThreatListResponse,
    ThreatRunDetailResponse,
    UserBehaviorResponse,
    UserBehaviorItem,
)
from app.services.threats.security_monitoring_service import SecurityMonitoringService

router = APIRouter(prefix="/threats", tags=["security-threats"])


def get_threat_service(db: AsyncSession = Depends(get_db)) -> SecurityMonitoringService:
    return SecurityMonitoringService(db)


@router.post("/detect", response_model=ThreatRunDetailResponse, status_code=status.HTTP_201_CREATED)
async def run_threat_detection(
    auth: AuthContext = Depends(require_permission(THREAT_MANAGE)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    run = await service.run_detection(triggered_by_user_id=auth.user.id)
    run = await service.repo.get_run(run.id)
    return ThreatRunDetailResponse(
        **ThreatDetectionRunResponse.model_validate(run).model_dump(),
        threats=[SecurityThreatResponse.model_validate(t) for t in (run.threats if run else [])],
    )


@router.get("/dashboard", response_model=ThreatDashboardResponse)
async def threat_dashboard(
    auth: AuthContext = Depends(require_any_permission(THREAT_READ, THREAT_READ_ALL)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    can_read_all = auth.has_permission(THREAT_READ_ALL)
    data = await service.get_dashboard(
        user_id=auth.user.id, can_read_all=can_read_all
    )
    latest = data["latest_run"]
    return ThreatDashboardResponse(
        open_threats=[SecurityThreatResponse.model_validate(t) for t in data["open_threats"]],
        open_total=data["open_total"],
        by_severity=data["by_severity"],
        by_type=data["by_type"],
        security_posture=data["security_posture"],
        latest_run=ThreatDetectionRunResponse.model_validate(latest) if latest else None,
    )


@router.get("", response_model=ThreatListResponse)
async def list_threats(
    severity: str | None = Query(default=None),
    threat_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(THREAT_READ, THREAT_READ_ALL)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    can_read_all = auth.has_permission(THREAT_READ_ALL)
    scope_user = None if can_read_all else auth.user.id
    items, total = await service.repo.list_open_threats(
        user_id=scope_user,
        severity=severity,
        threat_type=threat_type,
        limit=limit,
        offset=offset,
    )
    return ThreatListResponse(
        items=[SecurityThreatResponse.model_validate(t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/events", response_model=SecurityEventListResponse)
async def list_security_events(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(require_any_permission(THREAT_READ, THREAT_READ_ALL)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    can_read_all = auth.has_permission(THREAT_READ_ALL)
    scope_user = None if can_read_all else auth.user.id
    items, total = await service.repo.list_event_logs(
        user_id=scope_user, limit=limit, offset=offset
    )
    return SecurityEventListResponse(
        items=[SecurityEventLogResponse.model_validate(e) for e in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/behavior", response_model=UserBehaviorResponse)
async def user_behavior_analysis(
    auth: AuthContext = Depends(require_any_permission(THREAT_READ, THREAT_READ_ALL)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    can_read_all = auth.has_permission(THREAT_READ_ALL)
    items = await service.analyze_user_behavior(
        user_id=auth.user.id, can_read_all=can_read_all
    )
    return UserBehaviorResponse(items=[UserBehaviorItem.model_validate(i) for i in items])


@router.get("/runs/{run_id}", response_model=ThreatRunDetailResponse)
async def get_detection_run(
    run_id: UUID,
    auth: AuthContext = Depends(require_any_permission(THREAT_READ, THREAT_READ_ALL)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    run = await service.repo.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return ThreatRunDetailResponse(
        **ThreatDetectionRunResponse.model_validate(run).model_dump(),
        threats=[SecurityThreatResponse.model_validate(t) for t in run.threats],
    )


@router.get("/{threat_id}", response_model=SecurityThreatResponse)
async def get_threat(
    threat_id: UUID,
    auth: AuthContext = Depends(require_any_permission(THREAT_READ, THREAT_READ_ALL)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    threat = await service.repo.get_threat(threat_id)
    if threat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat not found")
    if (
        threat.user_id != auth.user.id
        and not auth.has_permission(THREAT_READ_ALL)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return SecurityThreatResponse.model_validate(threat)


@router.post("/{threat_id}/investigate", response_model=SecurityThreatResponse)
async def investigate_threat(
    threat_id: UUID,
    auth: AuthContext = Depends(require_permission(THREAT_MANAGE)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    try:
        threat = await service.investigate_threat(threat_id, auth.user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat not found") from None
    return SecurityThreatResponse.model_validate(threat)


@router.post("/{threat_id}/resolve", response_model=SecurityThreatResponse)
async def resolve_threat(
    threat_id: UUID,
    auth: AuthContext = Depends(require_permission(THREAT_MANAGE)),
    service: SecurityMonitoringService = Depends(get_threat_service),
):
    try:
        threat = await service.resolve_threat(threat_id, auth.user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat not found") from None
    return SecurityThreatResponse.model_validate(threat)

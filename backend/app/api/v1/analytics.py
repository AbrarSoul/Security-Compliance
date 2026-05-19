"""Analytics and monitoring dashboard APIs (Sprint 3 Step 7)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission
from app.core.permissions import ANALYTICS_READ, ANALYTICS_READ_ALL
from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    AnalyticsSummaryResponse,
    BlockedExecutionsResponse,
    HighRiskModelsResponse,
    HighRiskUsersResponse,
    OutputLeakageStatsResponse,
    PolicyViolationTrendResponse,
    PromptMonitoringStatsResponse,
    RealtimeViolationsResponse,
    RiskTrendResponse,
    TrendSeriesResponse,
)
from app.services.analytics.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


def _scope_and_range(
    auth: AuthContext,
    service: AnalyticsService,
    *,
    created_from: datetime | None,
    created_to: datetime | None,
    severity: str | None,
    default_days: int = 30,
):
    can_read_all = auth.has_permission(ANALYTICS_READ_ALL)
    scope = service.scope_for(user_id=auth.user.id, can_read_all=can_read_all)
    tr = service.time_range(
        created_from=created_from,
        created_to=created_to,
        severity=severity,
        default_days=default_days,
    )
    return scope, tr


@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def analytics_dashboard(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    severity: str | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(hour|day|week)$"),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Combined dashboard payload for charts and widgets."""
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=severity, default_days=days
    )
    return await service.get_dashboard(scope, tr, granularity=granularity)


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def analytics_summary(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    severity: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=severity, default_days=days
    )
    return await service.get_summary(scope, tr)


@router.get("/violations/realtime", response_model=RealtimeViolationsResponse)
async def realtime_violations(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    days: int = Query(default=7, ge=1, le=90),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=severity, default_days=days
    )
    return await service.get_realtime_violations(scope, tr, limit=limit)


@router.get("/trends/executions", response_model=TrendSeriesResponse)
async def execution_trends(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(hour|day|week)$"),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_execution_trend(scope, tr, granularity=granularity)


@router.get("/trends/risk", response_model=RiskTrendResponse)
async def risk_trends(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(hour|day|week)$"),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_risk_trend(scope, tr, granularity=granularity)


@router.get("/trends/violations", response_model=TrendSeriesResponse)
async def violation_trends(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    severity: str | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(hour|day|week)$"),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=severity, default_days=days
    )
    return await service.get_violation_trend(scope, tr, granularity=granularity)


@router.get("/trends/policy-violations", response_model=PolicyViolationTrendResponse)
async def policy_violation_trends(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(hour|day|week)$"),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_policy_violation_trend(scope, tr, granularity=granularity)


@router.get("/blocked-executions", response_model=BlockedExecutionsResponse)
async def blocked_executions(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    granularity: str = Query(default="day", pattern="^(hour|day|week)$"),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_blocked_executions(scope, tr, granularity=granularity)


@router.get("/prompt-monitoring", response_model=PromptMonitoringStatsResponse)
async def prompt_monitoring_stats(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_prompt_stats(scope, tr)


@router.get("/output-leakage", response_model=OutputLeakageStatsResponse)
async def output_leakage_stats(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_output_stats(scope, tr)


@router.get("/high-risk/users", response_model=HighRiskUsersResponse)
async def high_risk_users(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_high_risk_users(scope, tr, limit=limit)


@router.get("/high-risk/models", response_model=HighRiskModelsResponse)
async def high_risk_models(
    created_from: datetime | None = Query(default=None),
    created_to: datetime | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=30, ge=1, le=365),
    auth: AuthContext = Depends(require_any_permission(ANALYTICS_READ, ANALYTICS_READ_ALL)),
    service: AnalyticsService = Depends(get_analytics_service),
):
    scope, tr = _scope_and_range(
        auth, service, created_from=created_from, created_to=created_to, severity=None, default_days=days
    )
    return await service.get_high_risk_models(scope, tr, limit=limit)

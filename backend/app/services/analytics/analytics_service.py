"""Analytics aggregation service (Sprint 3 Step 7)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repository import (
    AnalyticsRepository,
    AnalyticsScope,
    AnalyticsTimeRange,
)
from app.schemas.analytics import (
    AnalyticsDashboardResponse,
    AnalyticsSummaryResponse,
    BlockedExecutionsResponse,
    CountSeriesPoint,
    HighRiskModelItem,
    HighRiskModelsResponse,
    HighRiskUserItem,
    HighRiskUsersResponse,
    LabelCount,
    OutputLeakageStatsResponse,
    PolicyViolationTrendResponse,
    PromptMonitoringStatsResponse,
    RealtimeViolationItem,
    RealtimeViolationsResponse,
    RiskTrendResponse,
    TimeSeriesPoint,
    TrendSeriesResponse,
)
from app.services.analytics.constants import VIOLATION_EVENT_TYPES
from app.services.events.constants import POLICY_VIOLATION


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.repo = AnalyticsRepository(db)

    def scope_for(self, *, user_id: UUID, can_read_all: bool) -> AnalyticsScope:
        if can_read_all:
            return AnalyticsScope(user_id=None)
        return AnalyticsScope(user_id=user_id)

    @staticmethod
    def time_range(
        *,
        created_from: datetime | None,
        created_to: datetime | None,
        severity: str | None = None,
        default_days: int = 30,
    ) -> AnalyticsTimeRange:
        now = datetime.now(UTC)
        start = created_from or (now - timedelta(days=default_days))
        end = created_to or now
        return AnalyticsTimeRange(
            created_from=start,
            created_to=end,
            severity=severity,
        )

    async def get_summary(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
    ) -> AnalyticsSummaryResponse:
        prompt_total = await self.repo.count_prompt_scans(scope, tr)
        output_total = await self.repo.count_output_scans(scope, tr)
        return AnalyticsSummaryResponse(
            violation_events=await self.repo.count_violation_events(scope, tr),
            blocked_executions=await self.repo.count_blocked_executions(scope, tr),
            policy_violations=await self.repo.count_policy_violations(scope, tr),
            prompt_scans_total=prompt_total,
            prompt_blocked=await self.repo.count_prompt_scans(scope, tr, decision="block"),
            output_scans_total=output_total,
            output_blocked=await self.repo.count_output_scans(scope, tr, decision="block"),
            avg_prompt_risk=await self.repo.avg_prompt_risk(scope, tr),
            avg_output_risk=await self.repo.avg_output_risk(scope, tr),
            unread_notifications=await self.repo.unread_notifications_count(scope),
            scope="organization" if scope.user_id is None else "user",
        )

    async def get_realtime_violations(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        limit: int = 25,
    ) -> RealtimeViolationsResponse:
        rows = await self.repo.list_realtime_violations(scope, tr, limit=limit)
        items = [
            RealtimeViolationItem(
                id=r.id,
                event_type=r.event_type,
                severity=r.severity,
                occurred_at=r.occurred_at,
                user_id=r.user_id,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                payload=r.payload_json,
            )
            for r in rows
        ]
        return RealtimeViolationsResponse(items=items, total=len(items))

    async def get_execution_trend(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> TrendSeriesResponse:
        raw = await self.repo.executions_time_series(scope, tr, granularity=granularity)
        return TrendSeriesResponse(
            metric="executions",
            granularity=granularity,
            points=[CountSeriesPoint(bucket=b, count=c) for b, c in raw],
        )

    async def get_risk_trend(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> RiskTrendResponse:
        raw = await self.repo.risk_time_series(scope, tr, granularity=granularity)
        return RiskTrendResponse(
            granularity=granularity,
            points=[TimeSeriesPoint(bucket=b, value=v) for b, v in raw],
        )

    async def get_violation_trend(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> TrendSeriesResponse:
        raw = await self.repo.events_time_series(
            scope,
            tr,
            event_types=VIOLATION_EVENT_TYPES,
            granularity=granularity,
        )
        return TrendSeriesResponse(
            metric="violations",
            granularity=granularity,
            points=[CountSeriesPoint(bucket=b, count=c) for b, c in raw],
        )

    async def get_prompt_stats(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
    ) -> PromptMonitoringStatsResponse:
        breakdown = await self.repo.prompt_decision_breakdown(scope, tr)
        counts = {label: count for label, count in breakdown}
        return PromptMonitoringStatsResponse(
            total_scans=sum(counts.values()),
            blocked=counts.get("block", 0),
            warned=counts.get("warn", 0),
            allowed=counts.get("allow", 0),
            decision_breakdown=[LabelCount(label=l, count=c) for l, c in breakdown],
            avg_risk_score=await self.repo.avg_prompt_risk(scope, tr),
        )

    async def get_output_stats(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
    ) -> OutputLeakageStatsResponse:
        breakdown = await self.repo.output_decision_breakdown(scope, tr)
        leakage = await self.repo.output_leakage_by_finding_type(scope, tr)
        counts = {label: count for label, count in breakdown}
        return OutputLeakageStatsResponse(
            total_scans=sum(counts.values()),
            blocked=counts.get("block", 0),
            warned=counts.get("warn", 0),
            leakage_breakdown=[LabelCount(label=l, count=c) for l, c in leakage],
            avg_risk_score=await self.repo.avg_output_risk(scope, tr),
        )

    async def get_blocked_executions(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> BlockedExecutionsResponse:
        status_rows = await self.repo.execution_status_breakdown(scope, tr)
        blocked_only = [
            (s, c)
            for s, c in status_rows
            if s in ("blocked", "interrupted")
        ]
        trend_raw = await self.repo.executions_time_series(scope, tr, granularity=granularity)
        return BlockedExecutionsResponse(
            total_blocked=sum(c for _, c in blocked_only),
            status_breakdown=[LabelCount(label=s, count=c) for s, c in blocked_only],
            trend=[CountSeriesPoint(bucket=b, count=c) for b, c in trend_raw],
        )

    async def get_high_risk_users(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        limit: int = 10,
    ) -> HighRiskUsersResponse:
        rows = await self.repo.high_risk_users(scope, tr, limit=limit)
        return HighRiskUsersResponse(
            items=[HighRiskUserItem.model_validate(r) for r in rows]
        )

    async def get_high_risk_models(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        limit: int = 10,
    ) -> HighRiskModelsResponse:
        rows = await self.repo.high_risk_models(scope, tr, limit=limit)
        return HighRiskModelsResponse(
            items=[HighRiskModelItem.model_validate(r) for r in rows]
        )

    async def get_policy_violation_trend(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> PolicyViolationTrendResponse:
        total = await self.repo.count_policy_violations(scope, tr)
        raw = await self.repo.policy_violation_time_series(scope, tr, granularity=granularity)
        return PolicyViolationTrendResponse(
            total=total,
            points=[CountSeriesPoint(bucket=b, count=c) for b, c in raw],
        )

    async def get_dashboard(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> AnalyticsDashboardResponse:
        summary = await self.get_summary(scope, tr)
        exec_trend = await self.get_execution_trend(scope, tr, granularity=granularity)
        risk_trend = await self.get_risk_trend(scope, tr, granularity=granularity)
        viol_trend = await self.get_violation_trend(scope, tr, granularity=granularity)
        policy_trend = await self.get_policy_violation_trend(scope, tr, granularity=granularity)
        prompt_stats = await self.get_prompt_stats(scope, tr)
        output_stats = await self.get_output_stats(scope, tr)
        blocked = await self.get_blocked_executions(scope, tr, granularity=granularity)
        realtime = await self.get_realtime_violations(scope, tr, limit=15)
        high_users = await self.get_high_risk_users(scope, tr)
        high_models = await self.get_high_risk_models(scope, tr)
        guard_rows = await self.repo.guard_action_breakdown(scope, tr)

        return AnalyticsDashboardResponse(
            summary=summary,
            execution_trend=exec_trend.points,
            risk_trend=risk_trend.points,
            violation_trend=viol_trend.points,
            policy_violation_trend=policy_trend.points,
            prompt_stats=prompt_stats,
            output_stats=output_stats,
            blocked_executions=blocked,
            realtime_violations=realtime.items,
            high_risk_users=high_users.items,
            high_risk_models=high_models.items,
            guard_actions=[LabelCount(label=l, count=c) for l, c in guard_rows],
        )

"""Aggregation queries for analytics dashboards."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_model import ComplianceModel
from app.models.domain_event import DomainEvent
from app.models.execution_request import ExecutionRequest
from app.models.guard_enforcement_log import GuardEnforcementLog
from app.models.notification import Notification
from app.models.output_scan import OutputScan
from app.models.prompt_scan import PromptScan
from app.models.user import User
from app.services.analytics.constants import (
    BLOCKED_EXECUTION_STATUSES,
    HIGH_RISK_SCORE_THRESHOLD,
    VIOLATION_EVENT_TYPES,
)
from app.services.events.constants import POLICY_VIOLATION


@dataclass(frozen=True)
class AnalyticsScope:
    user_id: UUID | None = None  # None = organization-wide


@dataclass(frozen=True)
class AnalyticsTimeRange:
    created_from: datetime | None = None
    created_to: datetime | None = None
    severity: str | None = None


class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _event_filters(
        self, query: Select, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> Select:
        if scope.user_id is not None:
            query = query.where(DomainEvent.user_id == scope.user_id)
        if tr.created_from is not None:
            query = query.where(DomainEvent.occurred_at >= tr.created_from)
        if tr.created_to is not None:
            query = query.where(DomainEvent.occurred_at <= tr.created_to)
        if tr.severity is not None:
            query = query.where(DomainEvent.severity == tr.severity)
        return query

    def _prompt_filters(
        self, query: Select, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> Select:
        if scope.user_id is not None:
            query = query.where(PromptScan.user_id == scope.user_id)
        if tr.created_from is not None:
            query = query.where(PromptScan.scanned_at >= tr.created_from)
        if tr.created_to is not None:
            query = query.where(PromptScan.scanned_at <= tr.created_to)
        return query

    def _output_filters(
        self, query: Select, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> Select:
        if scope.user_id is not None:
            query = query.where(OutputScan.user_id == scope.user_id)
        if tr.created_from is not None:
            query = query.where(OutputScan.scanned_at >= tr.created_from)
        if tr.created_to is not None:
            query = query.where(OutputScan.scanned_at <= tr.created_to)
        return query

    def _execution_filters(
        self, query: Select, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> Select:
        if scope.user_id is not None:
            query = query.where(ExecutionRequest.user_id == scope.user_id)
        if tr.created_from is not None:
            query = query.where(ExecutionRequest.created_at >= tr.created_from)
        if tr.created_to is not None:
            query = query.where(ExecutionRequest.created_at <= tr.created_to)
        return query

    async def count_violation_events(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> int:
        query = select(func.count()).select_from(DomainEvent).where(
            DomainEvent.event_type.in_(VIOLATION_EVENT_TYPES)
        )
        query = self._event_filters(query, scope, tr)
        return int((await self.db.execute(query)).scalar_one())

    async def count_blocked_executions(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> int:
        query = select(func.count()).select_from(ExecutionRequest).where(
            ExecutionRequest.status.in_(BLOCKED_EXECUTION_STATUSES)
        )
        query = self._execution_filters(query, scope, tr)
        return int((await self.db.execute(query)).scalar_one())

    async def count_prompt_scans(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange, *, decision: str | None = None
    ) -> int:
        query = select(func.count()).select_from(PromptScan)
        if decision:
            query = query.where(PromptScan.decision == decision)
        query = self._prompt_filters(query, scope, tr)
        return int((await self.db.execute(query)).scalar_one())

    async def count_output_scans(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange, *, decision: str | None = None
    ) -> int:
        query = select(func.count()).select_from(OutputScan)
        if decision:
            query = query.where(OutputScan.decision == decision)
        query = self._output_filters(query, scope, tr)
        return int((await self.db.execute(query)).scalar_one())

    async def count_policy_violations(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> int:
        query = select(func.count()).select_from(DomainEvent).where(
            DomainEvent.event_type == POLICY_VIOLATION
        )
        query = self._event_filters(query, scope, tr)
        return int((await self.db.execute(query)).scalar_one())

    async def avg_prompt_risk(self, scope: AnalyticsScope, tr: AnalyticsTimeRange) -> float | None:
        query = select(func.avg(PromptScan.risk_score))
        query = self._prompt_filters(query, scope, tr)
        val = (await self.db.execute(query)).scalar_one()
        return float(val) if val is not None else None

    async def avg_output_risk(self, scope: AnalyticsScope, tr: AnalyticsTimeRange) -> float | None:
        query = select(func.avg(OutputScan.risk_score))
        query = self._output_filters(query, scope, tr)
        val = (await self.db.execute(query)).scalar_one()
        return float(val) if val is not None else None

    async def prompt_decision_breakdown(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> list[tuple[str, int]]:
        query = (
            select(PromptScan.decision, func.count())
            .group_by(PromptScan.decision)
            .order_by(func.count().desc())
        )
        query = self._prompt_filters(query, scope, tr)
        rows = (await self.db.execute(query)).all()
        return [(str(r[0]), int(r[1])) for r in rows]

    async def output_decision_breakdown(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> list[tuple[str, int]]:
        query = (
            select(OutputScan.decision, func.count())
            .group_by(OutputScan.decision)
            .order_by(func.count().desc())
        )
        query = self._output_filters(query, scope, tr)
        rows = (await self.db.execute(query)).all()
        return [(str(r[0]), int(r[1])) for r in rows]

    async def output_leakage_by_finding_type(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange, *, limit: int = 10
    ) -> list[tuple[str, int]]:
        """Approximate leakage stats from blocked/warn output scan counts by decision."""
        query = (
            select(OutputScan.decision, func.count())
            .where(OutputScan.decision.in_(("block", "warn")))
            .group_by(OutputScan.decision)
        )
        query = self._output_filters(query, scope, tr)
        rows = (await self.db.execute(query)).all()
        return [(str(r[0]), int(r[1])) for r in rows[:limit]]

    async def execution_status_breakdown(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> list[tuple[str, int]]:
        query = (
            select(ExecutionRequest.status, func.count())
            .group_by(ExecutionRequest.status)
            .order_by(func.count().desc())
        )
        query = self._execution_filters(query, scope, tr)
        rows = (await self.db.execute(query)).all()
        return [(str(r[0]), int(r[1])) for r in rows]

    async def events_time_series(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        event_types: tuple[str, ...] | None = None,
        granularity: str = "day",
    ) -> list[tuple[datetime, int]]:
        bucket = func.date_trunc(granularity, DomainEvent.occurred_at).label("bucket")
        query = select(bucket, func.count()).group_by(bucket).order_by(bucket)
        if event_types:
            query = query.where(DomainEvent.event_type.in_(event_types))
        query = self._event_filters(query, scope, tr)
        rows = (await self.db.execute(query)).all()
        return [(r[0], int(r[1])) for r in rows if r[0] is not None]

    async def executions_time_series(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> list[tuple[datetime, int]]:
        bucket = func.date_trunc(granularity, ExecutionRequest.created_at).label("bucket")
        query = select(bucket, func.count()).group_by(bucket).order_by(bucket)
        query = self._execution_filters(query, scope, tr)
        rows = (await self.db.execute(query)).all()
        return [(r[0], int(r[1])) for r in rows if r[0] is not None]

    async def risk_time_series(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> list[tuple[datetime, float]]:
        prompt_bucket = func.date_trunc(granularity, PromptScan.scanned_at).label("bucket")
        p_query = select(
            prompt_bucket,
            func.avg(PromptScan.risk_score).label("avg_risk"),
        ).group_by(prompt_bucket)
        p_query = self._prompt_filters(p_query, scope, tr)

        rows = (await self.db.execute(p_query)).all()
        merged: dict[datetime, list[float]] = {}
        for bucket, avg in rows:
            if bucket is None or avg is None:
                continue
            merged.setdefault(bucket, []).append(float(avg))

        out_bucket = func.date_trunc(granularity, OutputScan.scanned_at).label("bucket")
        o_query = select(
            out_bucket,
            func.avg(OutputScan.risk_score).label("avg_risk"),
        ).group_by(out_bucket)
        o_query = self._output_filters(o_query, scope, tr)
        for bucket, avg in (await self.db.execute(o_query)).all():
            if bucket is None or avg is None:
                continue
            merged.setdefault(bucket, []).append(float(avg))

        return [
            (bucket, sum(vals) / len(vals))
            for bucket, vals in sorted(merged.items(), key=lambda x: x[0])
        ]

    async def policy_violation_time_series(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        granularity: str = "day",
    ) -> list[tuple[datetime, int]]:
        return await self.events_time_series(
            scope,
            tr,
            event_types=(POLICY_VIOLATION,),
            granularity=granularity,
        )

    async def list_realtime_violations(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        limit: int = 25,
    ) -> list[DomainEvent]:
        query = (
            select(DomainEvent)
            .where(DomainEvent.event_type.in_(VIOLATION_EVENT_TYPES))
            .order_by(DomainEvent.occurred_at.desc())
            .limit(limit)
        )
        query = self._event_filters(query, scope, tr)
        return list((await self.db.execute(query)).scalars().all())

    async def high_risk_users(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        limit: int = 10,
    ) -> list[dict]:
        """Users ranked by violation count and average risk from prompt scans."""
        subq = (
            select(
                PromptScan.user_id.label("uid"),
                func.count(PromptScan.id).label("scan_count"),
                func.avg(PromptScan.risk_score).label("avg_risk"),
                func.sum(
                    case((PromptScan.decision == "block", 1), else_=0)
                ).label("blocked_count"),
            )
            .group_by(PromptScan.user_id)
        )
        subq = self._prompt_filters(subq, scope, tr).subquery()

        query = (
            select(
                User.id,
                User.email,
                User.full_name,
                subq.c.scan_count,
                subq.c.avg_risk,
                subq.c.blocked_count,
            )
            .join(subq, subq.c.uid == User.id)
            .where(subq.c.avg_risk >= HIGH_RISK_SCORE_THRESHOLD)
            .order_by(subq.c.avg_risk.desc(), subq.c.blocked_count.desc())
            .limit(limit)
        )
        rows = (await self.db.execute(query)).all()
        return [
            {
                "user_id": r[0],
                "email": r[1],
                "full_name": r[2],
                "scan_count": int(r[3] or 0),
                "avg_risk_score": round(float(r[4] or 0), 1),
                "blocked_prompts": int(r[5] or 0),
            }
            for r in rows
        ]

    async def high_risk_models(
        self,
        scope: AnalyticsScope,
        tr: AnalyticsTimeRange,
        *,
        limit: int = 10,
    ) -> list[dict]:
        query = (
            select(
                ComplianceModel.id,
                ComplianceModel.name,
                ComplianceModel.provider,
                func.count(ExecutionRequest.id).label("execution_count"),
                func.sum(
                    case((ExecutionRequest.status.in_(BLOCKED_EXECUTION_STATUSES), 1), else_=0)
                ).label("blocked_count"),
            )
            .join(ExecutionRequest, ExecutionRequest.compliance_model_id == ComplianceModel.id)
            .group_by(ComplianceModel.id, ComplianceModel.name, ComplianceModel.provider)
        )
        query = self._execution_filters(query, scope, tr)
        query = query.having(
            func.sum(case((ExecutionRequest.status.in_(BLOCKED_EXECUTION_STATUSES), 1), else_=0))
            > 0
        ).order_by(
            func.sum(case((ExecutionRequest.status.in_(BLOCKED_EXECUTION_STATUSES), 1), else_=0)).desc()
        ).limit(limit)

        rows = (await self.db.execute(query)).all()
        return [
            {
                "model_id": r[0],
                "name": r[1],
                "provider": r[2],
                "execution_count": int(r[3] or 0),
                "blocked_count": int(r[4] or 0),
            }
            for r in rows
        ]

    async def guard_action_breakdown(
        self, scope: AnalyticsScope, tr: AnalyticsTimeRange
    ) -> list[tuple[str, int]]:
        query = (
            select(GuardEnforcementLog.action_taken, func.count())
            .group_by(GuardEnforcementLog.action_taken)
            .order_by(func.count().desc())
        )
        if scope.user_id is not None:
            query = query.where(GuardEnforcementLog.user_id == scope.user_id)
        if tr.created_from is not None:
            query = query.where(GuardEnforcementLog.created_at >= tr.created_from)
        if tr.created_to is not None:
            query = query.where(GuardEnforcementLog.created_at <= tr.created_to)
        rows = (await self.db.execute(query)).all()
        return [(str(r[0]), int(r[1])) for r in rows]

    async def unread_notifications_count(self, scope: AnalyticsScope) -> int:
        if scope.user_id is None:
            query = select(func.count()).select_from(Notification).where(
                Notification.is_read.is_(False)
            )
        else:
            query = select(func.count()).select_from(Notification).where(
                Notification.user_id == scope.user_id,
                Notification.is_read.is_(False),
            )
        return int((await self.db.execute(query)).scalar_one())

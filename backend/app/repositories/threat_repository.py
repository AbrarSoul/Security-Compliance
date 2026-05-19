"""Persistence for security threats and event logs."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.security_threat import SecurityEventLog, SecurityThreat, ThreatDetectionRun


class ThreatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_run(self, run: ThreatDetectionRun) -> ThreatDetectionRun:
        self.db.add(run)
        await self.db.flush()
        return run

    async def create_threat(self, threat: SecurityThreat) -> SecurityThreat:
        self.db.add(threat)
        await self.db.flush()
        return threat

    async def create_event_log(self, log: SecurityEventLog) -> SecurityEventLog:
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_threat(self, threat_id: UUID) -> SecurityThreat | None:
        result = await self.db.execute(
            select(SecurityThreat).where(SecurityThreat.id == threat_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_run(self) -> ThreatDetectionRun | None:
        result = await self.db.execute(
            select(ThreatDetectionRun)
            .options(selectinload(ThreatDetectionRun.threats))
            .order_by(ThreatDetectionRun.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_run(self, run_id: UUID) -> ThreatDetectionRun | None:
        result = await self.db.execute(
            select(ThreatDetectionRun)
            .options(selectinload(ThreatDetectionRun.threats))
            .where(ThreatDetectionRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_open_threats(
        self,
        *,
        user_id: UUID | None = None,
        severity: str | None = None,
        threat_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SecurityThreat], int]:
        base = select(SecurityThreat).where(SecurityThreat.status == "open")
        if user_id is not None:
            base = base.where(SecurityThreat.user_id == user_id)
        if severity:
            base = base.where(SecurityThreat.severity == severity)
        if threat_type:
            base = base.where(SecurityThreat.threat_type == threat_type)
        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_q)).scalar_one())
        result = await self.db.execute(
            base.order_by(SecurityThreat.threat_score.desc(), SecurityThreat.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_threats_for_run(self, run_id: UUID) -> list[SecurityThreat]:
        result = await self.db.execute(
            select(SecurityThreat)
            .where(SecurityThreat.detection_run_id == run_id)
            .order_by(SecurityThreat.threat_score.desc())
        )
        return list(result.scalars().all())

    async def list_event_logs(
        self,
        *,
        user_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[SecurityEventLog], int]:
        base = select(SecurityEventLog)
        if user_id is not None:
            base = base.where(SecurityEventLog.user_id == user_id)
        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_q)).scalar_one())
        result = await self.db.execute(
            base.order_by(SecurityEventLog.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_runs(self, *, limit: int = 20, offset: int = 0) -> tuple[list[ThreatDetectionRun], int]:
        total = int((await self.db.execute(select(func.count()).select_from(ThreatDetectionRun))).scalar_one())
        result = await self.db.execute(
            select(ThreatDetectionRun)
            .order_by(ThreatDetectionRun.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def update_threat_status(
        self, threat: SecurityThreat, status: str, *, resolved_at: datetime | None = None
    ) -> SecurityThreat:
        threat.status = status
        if resolved_at is not None:
            threat.resolved_at = resolved_at
        await self.db.flush()
        return threat

    async def count_threats_by_user(self, since: datetime) -> list[tuple[UUID, int, float]]:
        result = await self.db.execute(
            select(
                SecurityThreat.user_id,
                func.count(SecurityThreat.id),
                func.avg(SecurityThreat.threat_score),
            )
            .where(SecurityThreat.detected_at >= since, SecurityThreat.user_id.isnot(None))
            .group_by(SecurityThreat.user_id)
            .order_by(func.count(SecurityThreat.id).desc())
            .limit(20)
        )
        return [(r[0], int(r[1]), float(r[2] or 0)) for r in result.all() if r[0]]

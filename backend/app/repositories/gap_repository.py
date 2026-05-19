"""Persistence for gap analysis runs and findings."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.compliance_gap import ComplianceGap, GapAnalysisRun


class GapRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_run(self, run: GapAnalysisRun) -> GapAnalysisRun:
        self.db.add(run)
        await self.db.flush()
        return run

    async def create_gap(self, gap: ComplianceGap) -> ComplianceGap:
        self.db.add(gap)
        await self.db.flush()
        return gap

    async def get_run(self, run_id: UUID) -> GapAnalysisRun | None:
        result = await self.db.execute(
            select(GapAnalysisRun)
            .options(selectinload(GapAnalysisRun.gaps))
            .where(GapAnalysisRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_run(self) -> GapAnalysisRun | None:
        result = await self.db.execute(
            select(GapAnalysisRun)
            .options(selectinload(GapAnalysisRun.gaps))
            .order_by(GapAnalysisRun.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_runs(self, *, limit: int = 20, offset: int = 0) -> tuple[list[GapAnalysisRun], int]:
        count_q = select(func.count()).select_from(GapAnalysisRun)
        total = int((await self.db.execute(count_q)).scalar_one())
        result = await self.db.execute(
            select(GapAnalysisRun)
            .order_by(GapAnalysisRun.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_gaps_for_run(
        self,
        run_id: UUID,
        *,
        severity: str | None = None,
        gap_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ComplianceGap], int]:
        base = select(ComplianceGap).where(ComplianceGap.analysis_run_id == run_id)
        if severity:
            base = base.where(ComplianceGap.severity == severity)
        if gap_type:
            base = base.where(ComplianceGap.gap_type == gap_type)
        if status:
            base = base.where(ComplianceGap.status == status)

        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_q)).scalar_one())
        result = await self.db.execute(
            base.order_by(ComplianceGap.score.desc(), ComplianceGap.detected_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def list_gap_history(
        self,
        *,
        gap_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ComplianceGap], int]:
        base = select(ComplianceGap)
        if gap_type:
            base = base.where(ComplianceGap.gap_type == gap_type)
        if severity:
            base = base.where(ComplianceGap.severity == severity)
        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_q)).scalar_one())
        result = await self.db.execute(
            base.order_by(ComplianceGap.detected_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def get_gap(self, gap_id: UUID) -> ComplianceGap | None:
        result = await self.db.execute(select(ComplianceGap).where(ComplianceGap.id == gap_id))
        return result.scalar_one_or_none()

    async def update_gap_status(
        self, gap: ComplianceGap, status: str, *, resolved_at: datetime | None = None
    ) -> ComplianceGap:
        gap.status = status
        if resolved_at is not None:
            gap.resolved_at = resolved_at
        await self.db.flush()
        return gap

    async def find_open_gap_by_fingerprint(self, fingerprint: str) -> ComplianceGap | None:
        result = await self.db.execute(
            select(ComplianceGap)
            .where(ComplianceGap.fingerprint == fingerprint, ComplianceGap.status == "open")
            .order_by(ComplianceGap.detected_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

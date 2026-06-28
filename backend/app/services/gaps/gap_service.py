"""Compliance gap analysis orchestration."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_gap import ComplianceGap, GapAnalysisRun
from app.repositories.gap_repository import GapRepository
from app.services.audit_service import AuditService
from app.services.compliance.framework_mappings import attach_framework_refs_to_metadata
from app.services.gaps.constants import (
    GAP_STATUS_ACKNOWLEDGED,
    GAP_STATUS_OPEN,
    GAP_STATUS_RESOLVED,
    SCOPE_ORGANIZATION,
    SEVERITY_CRITICAL,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)
from app.services.gaps.gap_engine import GapAnalysisEngine
from app.services.gaps.scoring import aggregate_run_score, score_for_severity
from app.services.gaps.types import GapFinding


class GapAnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GapRepository(db)
        self.audit = AuditService(db)

    async def run_analysis(self, *, triggered_by_user_id: UUID | None) -> GapAnalysisRun:
        engine = GapAnalysisEngine(self.db)
        findings = await engine.run_all()

        run = GapAnalysisRun(
            triggered_by_user_id=triggered_by_user_id,
            scope=SCOPE_ORGANIZATION,
            started_at=datetime.now(UTC),
        )
        await self.repo.create_run(run)

        counts = {SEVERITY_CRITICAL: 0, SEVERITY_HIGH: 0, SEVERITY_MEDIUM: 0, SEVERITY_LOW: 0}
        gaps: list[ComplianceGap] = []

        for finding in findings:
            score = score_for_severity(finding.severity)
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
            gap = ComplianceGap(
                analysis_run_id=run.id,
                gap_type=finding.gap_type,
                category=finding.category,
                severity=finding.severity,
                score=score,
                title=finding.title,
                description=finding.description,
                recommendation=finding.recommendation,
                status=GAP_STATUS_OPEN,
                fingerprint=finding.fingerprint(),
                resource_type=finding.resource_type,
                resource_id=finding.resource_id,
                metadata_json=attach_framework_refs_to_metadata(
                    finding.gap_type, finding.metadata or None
                ),
            )
            await self.repo.create_gap(gap)
            gaps.append(gap)
            await self.audit.log_gap_detected(
                user_id=triggered_by_user_id,
                gap_id=gap.id,
                gap_type=finding.gap_type,
                severity=finding.severity,
                metadata={"title": finding.title, "fingerprint": gap.fingerprint},
            )

        run.gaps_found = len(gaps)
        run.critical_count = counts.get(SEVERITY_CRITICAL, 0)
        run.high_count = counts.get(SEVERITY_HIGH, 0)
        run.medium_count = counts.get(SEVERITY_MEDIUM, 0)
        run.low_count = counts.get(SEVERITY_LOW, 0)
        run.completed_at = datetime.now(UTC)
        run.summary_json = {
            "posture_score": aggregate_run_score(gaps),
            "gap_types": list({g.gap_type for g in gaps}),
        }
        await self.db.flush()

        await self.audit.log_gap_analysis_run(
            user_id=triggered_by_user_id,
            run_id=run.id,
            gaps_found=run.gaps_found,
            metadata=run.summary_json,
        )
        return run

    async def get_latest(self) -> GapAnalysisRun | None:
        return await self.repo.get_latest_run()

    async def get_run(self, run_id: UUID) -> GapAnalysisRun | None:
        return await self.repo.get_run(run_id)

    async def list_runs(self, *, limit: int = 20, offset: int = 0):
        return await self.repo.list_runs(limit=limit, offset=offset)

    async def list_current_gaps(
        self,
        *,
        severity: str | None = None,
        gap_type: str | None = None,
        status: str | None = GAP_STATUS_OPEN,
        limit: int = 100,
        offset: int = 0,
    ):
        run = await self.repo.get_latest_run()
        if run is None:
            return [], 0, None
        items, total = await self.repo.list_gaps_for_run(
            run.id,
            severity=severity,
            gap_type=gap_type,
            status=status,
            limit=limit,
            offset=offset,
        )
        return items, total, run

    async def list_history(
        self,
        *,
        gap_type: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        return await self.repo.list_gap_history(
            gap_type=gap_type, severity=severity, limit=limit, offset=offset
        )

    async def acknowledge_gap(self, gap_id: UUID, user_id: UUID) -> ComplianceGap:
        gap = await self.repo.get_gap(gap_id)
        if gap is None:
            raise ValueError("Gap not found")
        await self.repo.update_gap_status(gap, GAP_STATUS_ACKNOWLEDGED)
        await self.audit.log_gap_status_change(
            user_id=user_id, gap_id=gap.id, new_status=GAP_STATUS_ACKNOWLEDGED
        )
        return gap

    async def get_gap(self, gap_id: UUID) -> ComplianceGap | None:
        return await self.repo.get_gap(gap_id)

    async def resolve_gap(self, gap_id: UUID, user_id: UUID) -> ComplianceGap:
        gap = await self.repo.get_gap(gap_id)
        if gap is None:
            raise ValueError("Gap not found")
        await self.repo.update_gap_status(
            gap, GAP_STATUS_RESOLVED, resolved_at=datetime.now(UTC)
        )
        await self.audit.log_gap_status_change(
            user_id=user_id, gap_id=gap.id, new_status=GAP_STATUS_RESOLVED
        )
        return gap

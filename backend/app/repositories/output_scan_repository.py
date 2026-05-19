from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.output_scan import OutputScan


class OutputScanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, scan: OutputScan) -> OutputScan:
        self.db.add(scan)
        await self.db.flush()
        return scan

    async def get_by_id(self, scan_id: UUID) -> OutputScan | None:
        result = await self.db.execute(select(OutputScan).where(OutputScan.id == scan_id))
        return result.scalar_one_or_none()

    async def get_for_user(self, scan_id: UUID, user_id: UUID) -> OutputScan | None:
        result = await self.db.execute(
            select(OutputScan).where(OutputScan.id == scan_id, OutputScan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_scans(
        self,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        decision: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OutputScan]:
        query: Select = select(OutputScan).order_by(OutputScan.scanned_at.desc())
        if user_id is not None:
            query = query.where(OutputScan.user_id == user_id)
        if session_id is not None:
            query = query.where(OutputScan.session_id == session_id)
        if decision is not None:
            query = query.where(OutputScan.decision == decision)
        result = await self.db.execute(query.limit(limit).offset(offset))
        return list(result.scalars().all())

    async def count_scans(
        self,
        *,
        user_id: UUID | None = None,
        session_id: UUID | None = None,
        decision: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(OutputScan)
        if user_id is not None:
            query = query.where(OutputScan.user_id == user_id)
        if session_id is not None:
            query = query.where(OutputScan.session_id == session_id)
        if decision is not None:
            query = query.where(OutputScan.decision == decision)
        result = await self.db.execute(query)
        return int(result.scalar_one())

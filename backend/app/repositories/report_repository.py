from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report
from app.models.scan import Scan


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_scan_id(self, scan_id: UUID) -> Report | None:
        result = await self.db.execute(select(Report).where(Report.scan_id == scan_id))
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, report_id: UUID, user_id: UUID) -> Report | None:
        result = await self.db.execute(
            select(Report)
            .options(selectinload(Report.scan).selectinload(Scan.file))
            .where(Report.id == report_id, Report.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, report_id: UUID) -> Report | None:
        result = await self.db.execute(
            select(Report)
            .options(selectinload(Report.scan).selectinload(Scan.file))
            .where(Report.id == report_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID, *, limit: int = 50, offset: int = 0) -> list[Report]:
        result = await self.db.execute(
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[Report]:
        result = await self.db.execute(
            select(Report).order_by(Report.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, report: Report) -> Report:
        self.db.add(report)
        await self.db.flush()
        return report

    async def delete(self, report: Report) -> None:
        await self.db.delete(report)

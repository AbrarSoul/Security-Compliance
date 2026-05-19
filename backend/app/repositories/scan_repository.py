from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.file import File
from app.models.scan import Scan
from app.models.scan_finding import ScanFinding
from app.models.scan_recommendation import ScanRecommendation


class ScanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, *, scan_id: UUID, user_id: UUID, file_id: UUID) -> Scan:
        scan = Scan(id=scan_id, user_id=user_id, file_id=file_id, status="pending")
        self.db.add(scan)
        await self.db.flush()
        return scan

    async def add_findings(self, findings: list[ScanFinding]) -> None:
        self.db.add_all(findings)
        await self.db.flush()

    async def add_recommendations(self, recommendations: list[ScanRecommendation]) -> None:
        self.db.add_all(recommendations)
        await self.db.flush()

    async def get_by_id(self, scan_id: UUID) -> Scan | None:
        result = await self.db.execute(
            select(Scan)
            .options(
                selectinload(Scan.findings),
                selectinload(Scan.recommendations),
                selectinload(Scan.file).selectinload(File.metadata_row),
            )
            .where(Scan.id == scan_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(self, scan_id: UUID, user_id: UUID) -> Scan | None:
        result = await self.db.execute(
            select(Scan)
            .options(
                selectinload(Scan.findings),
                selectinload(Scan.recommendations),
                selectinload(Scan.file).selectinload(File.metadata_row),
            )
            .where(Scan.id == scan_id, Scan.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[Scan]:
        result = await self.db.execute(
            select(Scan)
            .options(selectinload(Scan.findings))
            .where(Scan.user_id == user_id)
            .order_by(Scan.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_scan(self, scan: Scan) -> Scan:
        await self.db.flush()
        return scan

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guard_enforcement_log import GuardEnforcementLog


class GuardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(self, log: GuardEnforcementLog) -> GuardEnforcementLog:
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_for_execution(
        self, execution_request_id: UUID, *, limit: int = 50
    ) -> list[GuardEnforcementLog]:
        result = await self.db.execute(
            select(GuardEnforcementLog)
            .where(GuardEnforcementLog.execution_request_id == execution_request_id)
            .order_by(GuardEnforcementLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

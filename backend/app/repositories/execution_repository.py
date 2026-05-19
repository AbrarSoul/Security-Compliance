from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.execution_request import ExecutionRequest
from app.models.execution_result import ExecutionResult
from app.models.scan import Scan


class ExecutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _detail_query(self) -> Select:
        return select(ExecutionRequest).options(
            selectinload(ExecutionRequest.execution_result),
            selectinload(ExecutionRequest.compliance_model),
            selectinload(ExecutionRequest.scan).selectinload(Scan.findings),
            selectinload(ExecutionRequest.file),
            selectinload(ExecutionRequest.model_validation),
        )

    async def create_request(self, request: ExecutionRequest) -> ExecutionRequest:
        self.db.add(request)
        await self.db.flush()
        return request

    async def create_result(self, result: ExecutionResult) -> ExecutionResult:
        self.db.add(result)
        await self.db.flush()
        return result

    async def update_request(self, request: ExecutionRequest) -> ExecutionRequest:
        await self.db.flush()
        return request

    async def get_request_by_id(self, request_id: UUID) -> ExecutionRequest | None:
        result = await self.db.execute(
            self._detail_query().where(ExecutionRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_request_for_user(
        self, request_id: UUID, user_id: UUID
    ) -> ExecutionRequest | None:
        result = await self.db.execute(
            self._detail_query().where(
                ExecutionRequest.id == request_id,
                ExecutionRequest.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> list[ExecutionRequest]:
        result = await self.db.execute(
            self._detail_query()
            .where(ExecutionRequest.user_id == user_id)
            .order_by(ExecutionRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().unique().all())

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> list[ExecutionRequest]:
        result = await self.db.execute(
            self._detail_query()
            .order_by(ExecutionRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().unique().all())

    async def count_by_user(self, user_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(ExecutionRequest)
            .where(ExecutionRequest.user_id == user_id)
        )
        return int(result.scalar_one())

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(ExecutionRequest))
        return int(result.scalar_one())

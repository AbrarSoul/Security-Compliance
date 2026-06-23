from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_model import ComplianceModel


class ComplianceModelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, model_id: UUID) -> ComplianceModel | None:
        result = await self.db.execute(
            select(ComplianceModel).where(ComplianceModel.id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> ComplianceModel | None:
        result = await self.db.execute(
            select(ComplianceModel).where(ComplianceModel.code == code)
        )
        return result.scalar_one_or_none()

    async def list_by_code_prefix(self, prefix: str) -> list[ComplianceModel]:
        result = await self.db.execute(
            select(ComplianceModel)
            .where(ComplianceModel.code.startswith(prefix))
            .order_by(ComplianceModel.name.asc())
        )
        return list(result.scalars().all())

    async def list_models(
        self,
        *,
        active_only: bool = True,
        approved_only: bool = False,
        model_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ComplianceModel]:
        query = (
            select(ComplianceModel)
            .order_by(ComplianceModel.name.asc())
            .limit(limit)
            .offset(offset)
        )
        query = self._apply_filters(
            query, active_only=active_only, approved_only=approved_only, model_type=model_type
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_models(
        self,
        *,
        active_only: bool = True,
        approved_only: bool = False,
        model_type: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(ComplianceModel)
        query = self._apply_filters(
            query, active_only=active_only, approved_only=approved_only, model_type=model_type
        )
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def create(self, model: ComplianceModel) -> ComplianceModel:
        self.db.add(model)
        await self.db.flush()
        return model

    async def update(self, model: ComplianceModel) -> ComplianceModel:
        await self.db.flush()
        return model

    def _apply_filters(
        self,
        query: Select,
        *,
        active_only: bool,
        approved_only: bool,
        model_type: str | None,
    ) -> Select:
        if active_only:
            query = query.where(ComplianceModel.is_active.is_(True))
        if approved_only:
            query = query.where(ComplianceModel.is_approved.is_(True))
        if model_type is not None:
            query = query.where(ComplianceModel.model_type == model_type)
        return query

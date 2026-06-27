from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.model_validation import ModelValidation
from app.models.scan import Scan


class ModelValidationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, validation: ModelValidation) -> ModelValidation:
        self.db.add(validation)
        await self.db.flush()
        return validation

    async def get_by_id(self, validation_id: UUID) -> ModelValidation | None:
        result = await self.db.execute(
            select(ModelValidation)
            .options(
                selectinload(ModelValidation.compliance_model),
                selectinload(ModelValidation.scan).selectinload(Scan.findings),
            )
            .where(ModelValidation.id == validation_id)
        )
        return result.scalar_one_or_none()

    async def update(self, validation: ModelValidation) -> ModelValidation:
        await self.db.flush()
        return validation

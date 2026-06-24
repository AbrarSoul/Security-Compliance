"""Persistence for GAIRA applications and assessments."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.gaira import AIApplication, GairaAssessment


class GairaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_application(self, application: AIApplication) -> AIApplication:
        self.db.add(application)
        await self.db.flush()
        return application

    async def get_application(self, application_id: UUID) -> AIApplication | None:
        result = await self.db.execute(
            select(AIApplication)
            .options(
                selectinload(AIApplication.assessments),
                selectinload(AIApplication.compliance_model),
            )
            .where(AIApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    async def list_applications(
        self,
        *,
        active_only: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AIApplication], int]:
        base = select(AIApplication)
        if active_only:
            base = base.where(AIApplication.is_active.is_(True))
        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self.db.execute(count_q)).scalar_one())
        result = await self.db.execute(
            base.order_by(AIApplication.updated_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def update_application(self, application: AIApplication) -> AIApplication:
        await self.db.flush()
        return application

    async def create_assessment(self, assessment: GairaAssessment) -> GairaAssessment:
        self.db.add(assessment)
        await self.db.flush()
        return assessment

    async def get_assessment(self, assessment_id: UUID) -> GairaAssessment | None:
        result = await self.db.execute(
            select(GairaAssessment)
            .options(
                selectinload(GairaAssessment.application),
                selectinload(GairaAssessment.scan),
            )
            .where(GairaAssessment.id == assessment_id)
        )
        return result.scalar_one_or_none()

    async def list_assessments_for_application(
        self, application_id: UUID
    ) -> list[GairaAssessment]:
        result = await self.db.execute(
            select(GairaAssessment)
            .where(GairaAssessment.application_id == application_id)
            .order_by(GairaAssessment.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_submitted_assessment(
        self, application_id: UUID, assessment_type: str | None = None
    ) -> GairaAssessment | None:
        query = (
            select(GairaAssessment)
            .where(
                GairaAssessment.application_id == application_id,
                GairaAssessment.status == "submitted",
            )
            .order_by(GairaAssessment.submitted_at.desc())
            .limit(1)
        )
        if assessment_type:
            query = query.where(GairaAssessment.assessment_type == assessment_type)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_assessment(self, assessment: GairaAssessment) -> GairaAssessment:
        await self.db.flush()
        return assessment

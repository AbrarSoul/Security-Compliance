from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_rule import ComplianceRule


class ComplianceRuleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, rule_id: UUID) -> ComplianceRule | None:
        result = await self.db.execute(
            select(ComplianceRule).where(ComplianceRule.id == rule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> ComplianceRule | None:
        result = await self.db.execute(
            select(ComplianceRule).where(ComplianceRule.code == code)
        )
        return result.scalar_one_or_none()

    async def list_rules(
        self,
        *,
        category: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ComplianceRule]:
        query = select(ComplianceRule).order_by(
            ComplianceRule.priority.desc(),
            ComplianceRule.name.asc(),
        )
        query = self._apply_filters(query, category=category, enabled_only=enabled_only)
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_rules(
        self,
        *,
        category: str | None = None,
        enabled_only: bool = False,
    ) -> int:
        query = select(func.count()).select_from(ComplianceRule)
        query = self._apply_filters(query, category=category, enabled_only=enabled_only)
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def list_enabled_for_evaluation(self) -> list[ComplianceRule]:
        result = await self.db.execute(
            select(ComplianceRule)
            .where(ComplianceRule.is_enabled.is_(True))
            .order_by(ComplianceRule.priority.desc(), ComplianceRule.name.asc())
        )
        return list(result.scalars().all())

    async def create(self, rule: ComplianceRule) -> ComplianceRule:
        self.db.add(rule)
        await self.db.flush()
        return rule

    async def update(self, rule: ComplianceRule) -> ComplianceRule:
        await self.db.flush()
        return rule

    def _apply_filters(
        self,
        query: Select,
        *,
        category: str | None,
        enabled_only: bool,
    ) -> Select:
        if category is not None:
            query = query.where(ComplianceRule.category == category)
        if enabled_only:
            query = query.where(ComplianceRule.is_enabled.is_(True))
        return query

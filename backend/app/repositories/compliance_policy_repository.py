from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.compliance_policy import CompliancePolicy
from app.models.compliance_rule import ComplianceRule
from app.models.policy_rule import PolicyRule
from app.services.policies.constants import ACTIVE_POLICY_STATUS


class CompliancePolicyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _with_rules(self, query: Select) -> Select:
        return query.options(
            selectinload(CompliancePolicy.policy_rule_links).selectinload(PolicyRule.rule)
        )

    async def get_by_id(self, policy_id: UUID, *, load_rules: bool = True) -> CompliancePolicy | None:
        query = select(CompliancePolicy).where(CompliancePolicy.id == policy_id)
        if load_rules:
            query = self._with_rules(query)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_policies(
        self,
        *,
        status: str | None = None,
        policy_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CompliancePolicy]:
        query = (
            select(CompliancePolicy)
            .order_by(CompliancePolicy.priority.desc(), CompliancePolicy.name.asc())
            .limit(limit)
            .offset(offset)
        )
        query = self._with_rules(query)
        query = self._apply_filters(query, status=status, policy_type=policy_type)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def list_active_policies(self) -> list[CompliancePolicy]:
        query = (
            select(CompliancePolicy)
            .where(CompliancePolicy.status == ACTIVE_POLICY_STATUS)
            .order_by(CompliancePolicy.priority.desc(), CompliancePolicy.name.asc())
        )
        query = self._with_rules(query)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def count_policies(
        self,
        *,
        status: str | None = None,
        policy_type: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(CompliancePolicy)
        query = self._apply_filters(query, status=status, policy_type=policy_type)
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def create(self, policy: CompliancePolicy) -> CompliancePolicy:
        self.db.add(policy)
        await self.db.flush()
        return policy

    async def update(self, policy: CompliancePolicy) -> CompliancePolicy:
        await self.db.flush()
        return policy

    async def get_rules_by_ids(self, rule_ids: list[UUID]) -> list[ComplianceRule]:
        if not rule_ids:
            return []
        result = await self.db.execute(
            select(ComplianceRule).where(ComplianceRule.id.in_(rule_ids))
        )
        return list(result.scalars().all())

    async def attach_rule(
        self,
        policy_id: UUID,
        rule_id: UUID,
        *,
        sort_order: int = 0,
    ) -> PolicyRule:
        link = PolicyRule(
            policy_id=policy_id,
            rule_id=rule_id,
            sort_order=sort_order,
        )
        self.db.add(link)
        await self.db.flush()
        return link

    async def detach_rule(self, policy_id: UUID, rule_id: UUID) -> bool:
        result = await self.db.execute(
            select(PolicyRule).where(
                PolicyRule.policy_id == policy_id,
                PolicyRule.rule_id == rule_id,
            )
        )
        link = result.scalar_one_or_none()
        if link is None:
            return False
        await self.db.delete(link)
        await self.db.flush()
        return True

    async def has_rule_link(self, policy_id: UUID, rule_id: UUID) -> bool:
        result = await self.db.execute(
            select(func.count())
            .select_from(PolicyRule)
            .where(
                PolicyRule.policy_id == policy_id,
                PolicyRule.rule_id == rule_id,
            )
        )
        return int(result.scalar_one()) > 0

    def _apply_filters(
        self,
        query: Select,
        *,
        status: str | None,
        policy_type: str | None,
    ) -> Select:
        if status is not None:
            query = query.where(CompliancePolicy.status == status)
        if policy_type is not None:
            query = query.where(CompliancePolicy.policy_type == policy_type)
        return query

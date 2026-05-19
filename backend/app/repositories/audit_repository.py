from datetime import datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog


class AuditLogFilters:
    def __init__(
        self,
        *,
        user_id: UUID | None = None,
        action: str | None = None,
        action_prefix: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        resource_type: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ):
        self.user_id = user_id
        self.action = action
        self.action_prefix = action_prefix
        self.severity = severity
        self.status = status
        self.resource_type = resource_type
        self.created_from = created_from
        self.created_to = created_to


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, entry: AuditLog) -> AuditLog:
        self.db.add(entry)
        await self.db.flush()
        return entry

    def _apply_filters(self, query: Select, filters: AuditLogFilters) -> Select:
        if filters.user_id is not None:
            query = query.where(AuditLog.user_id == filters.user_id)
        if filters.action is not None:
            query = query.where(AuditLog.action == filters.action)
        if filters.action_prefix is not None:
            query = query.where(AuditLog.action.startswith(filters.action_prefix))
        if filters.severity is not None:
            query = query.where(AuditLog.severity == filters.severity)
        if filters.status is not None:
            query = query.where(AuditLog.status == filters.status)
        if filters.resource_type is not None:
            query = query.where(AuditLog.resource_type == filters.resource_type)
        if filters.created_from is not None:
            query = query.where(AuditLog.created_at >= filters.created_from)
        if filters.created_to is not None:
            query = query.where(AuditLog.created_at <= filters.created_to)
        return query

    async def list_filtered(
        self,
        filters: AuditLogFilters,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        query = (
            select(AuditLog)
            .options(selectinload(AuditLog.user))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        query = self._apply_filters(query, filters)
        result = await self.db.execute(query)
        return list(result.scalars().unique().all())

    async def count_filtered(self, filters: AuditLogFilters) -> int:
        query = select(func.count()).select_from(AuditLog)
        query = self._apply_filters(query, filters)
        result = await self.db.execute(query)
        return int(result.scalar_one())

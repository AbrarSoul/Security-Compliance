"""Final allow / warn / block outcome and evaluation payload for an execution request."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.execution_request import ExecutionRequest


class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    execution_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("execution_requests.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    decision: Mapped[str | None] = mapped_column(
        String(16), nullable=True, index=True
    )
    risk_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    reason_codes_json: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
    )
    evaluation_summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    blocking_reasons_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    warning_reasons_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommendations_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="pending", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    execution_request: Mapped["ExecutionRequest"] = relationship(
        "ExecutionRequest", back_populates="execution_result"
    )

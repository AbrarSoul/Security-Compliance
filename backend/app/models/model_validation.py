"""Model compliance validation results (standalone or execution-linked)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.compliance_model import ComplianceModel
    from app.models.execution_request import ExecutionRequest
    from app.models.scan import Scan
    from app.models.user import User


class ModelValidation(Base):
    __tablename__ = "model_validations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    execution_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("execution_requests.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    compliance_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="pending", index=True
    )
    decision: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)
    risk_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    risk_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    primary_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    flags_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    details_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommendations_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    execution_request: Mapped["ExecutionRequest | None"] = relationship(
        "ExecutionRequest", back_populates="model_validation"
    )
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    scan: Mapped["Scan | None"] = relationship("Scan", back_populates="model_validations")
    compliance_model: Mapped["ComplianceModel | None"] = relationship(
        "ComplianceModel", back_populates="validations"
    )

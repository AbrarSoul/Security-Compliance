"""User intent to run an operation against a dataset with a declared model (pre-execution)."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.compliance_model import ComplianceModel
    from app.models.execution_result import ExecutionResult
    from app.models.file import File
    from app.models.model_validation import ModelValidation
    from app.models.scan import Scan
    from app.models.user import User


class ExecutionRequest(Base):
    __tablename__ = "execution_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    compliance_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_external_api: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="pending_validation", index=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="execution_requests"
    )
    acknowledged_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[acknowledged_by_user_id]
    )
    file: Mapped["File"] = relationship("File", back_populates="execution_requests")
    scan: Mapped["Scan | None"] = relationship("Scan", back_populates="execution_requests")
    compliance_model: Mapped["ComplianceModel | None"] = relationship(
        "ComplianceModel", foreign_keys=[compliance_model_id]
    )
    model_validation: Mapped["ModelValidation | None"] = relationship(
        "ModelValidation",
        back_populates="execution_request",
        uselist=False,
        cascade="all, delete-orphan",
    )
    execution_result: Mapped["ExecutionResult | None"] = relationship(
        "ExecutionResult",
        back_populates="execution_request",
        uselist=False,
        cascade="all, delete-orphan",
    )

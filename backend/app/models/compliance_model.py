"""Registered AI model metadata for compliance validation."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.model_validation import ModelValidation
    from app.models.user import User


class ComplianceModel(Base):
    __tablename__ = "compliance_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    endpoint_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_retention_policy: Mapped[str | None] = mapped_column(Text, nullable=True)
    logging_enabled: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    data_leaves_platform: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true", index=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    created_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[created_by_user_id]
    )
    validations: Mapped[list["ModelValidation"]] = relationship(
        "ModelValidation", back_populates="compliance_model"
    )

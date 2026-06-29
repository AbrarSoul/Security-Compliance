"""GAIRA AI risk assessment models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.compliance_model import ComplianceModel
    from app.models.scan import Scan
    from app.models.user import User


class AIApplication(Base):
    """ROAIA registry entry for an AI use case / application."""

    __tablename__ = "ai_applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    audience: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope_includes: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope_excludes: Mapped[str | None] = mapped_column(Text, nullable=True)
    technology_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(255), nullable=True)
    compliance_model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_act_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    gaira_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="none", index=True
    )
    compliance_check_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="none"
    )
    dpia_status: Mapped[str] = mapped_column(String(32), nullable=False, server_default="none")
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_assessment_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registration_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="approved", index=True
    )
    auditor_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    auditor_reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    auditor_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true", index=True)
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

    compliance_model: Mapped["ComplianceModel | None"] = relationship("ComplianceModel")
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    auditor_reviewed_by: Mapped["User | None"] = relationship(
        "User", foreign_keys=[auditor_reviewed_by_user_id]
    )
    approved_by: Mapped["User | None"] = relationship("User", foreign_keys=[approved_by_user_id])
    rejected_by: Mapped["User | None"] = relationship("User", foreign_keys=[rejected_by_user_id])
    assessments: Mapped[list["GairaAssessment"]] = relationship(
        "GairaAssessment", back_populates="application", cascade="all, delete-orphan"
    )


class GairaAssessment(Base):
    """A GAIRA assessment run for an AI application."""

    __tablename__ = "gaira_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessment_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="draft", index=True
    )
    framework_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_step: Mapped[str | None] = mapped_column(String(16), nullable=True)
    answers_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    computed_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    overall_risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    proceed_decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    application: Mapped["AIApplication"] = relationship("AIApplication", back_populates="assessments")
    scan: Mapped["Scan | None"] = relationship("Scan")
    created_by: Mapped["User | None"] = relationship("User", foreign_keys=[created_by_user_id])
    decision_by: Mapped["User | None"] = relationship("User", foreign_keys=[decision_by_user_id])

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.execution_request import ExecutionRequest
    from app.models.file import File
    from app.models.report import Report
    from app.models.model_validation import ModelValidation
    from app.models.scan_finding import ScanFinding
    from app.models.scan_recommendation import ScanRecommendation
    from app.models.user import User


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    risk_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    compliance_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    classification: Mapped[str | None] = mapped_column(String(32), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_breakdown_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    rule_evaluation_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="scans")
    file: Mapped["File"] = relationship("File", back_populates="scans")
    findings: Mapped[list["ScanFinding"]] = relationship(
        "ScanFinding", back_populates="scan", cascade="all, delete-orphan"
    )
    recommendations: Mapped[list["ScanRecommendation"]] = relationship(
        "ScanRecommendation", back_populates="scan", cascade="all, delete-orphan"
    )
    report: Mapped["Report | None"] = relationship(
        "Report", back_populates="scan", uselist=False, cascade="all, delete-orphan"
    )
    execution_requests: Mapped[list["ExecutionRequest"]] = relationship(
        "ExecutionRequest", back_populates="scan"
    )
    model_validations: Mapped[list["ModelValidation"]] = relationship(
        "ModelValidation", back_populates="scan"
    )

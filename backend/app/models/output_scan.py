"""Persisted result of real-time output compliance scanning."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.monitoring_session import MonitoringSession
    from app.models.user import User


class OutputScan(Base):
    __tablename__ = "output_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitoring_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    execution_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("execution_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prompt_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_scans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    output_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(16), nullable=False)
    findings_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    masked_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    redacted_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocking_reasons_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    warning_reasons_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recommendations_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    session: Mapped["MonitoringSession | None"] = relationship(
        "MonitoringSession",
        foreign_keys=[session_id],
    )

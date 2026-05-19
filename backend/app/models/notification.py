"""In-app and email notification records."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false", index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    email_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # noqa: F821


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    email_min_severity: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="high"
    )
    dashboard_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_prompt_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    notify_output_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    notify_policy_violation: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    notify_suspicious_activity: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_high_risk_execution: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_repeated_violation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    notify_system_security: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

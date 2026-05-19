"""Associates compliance policies with compliance rules and optional ordering."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.compliance_policy import CompliancePolicy
    from app.models.compliance_rule import ComplianceRule


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_policies.id", ondelete="CASCADE"),
        primary_key=True,
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_rules.id", ondelete="CASCADE"),
        primary_key=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    policy: Mapped["CompliancePolicy"] = relationship(
        "CompliancePolicy", back_populates="policy_rule_links"
    )
    rule: Mapped["ComplianceRule"] = relationship(
        "ComplianceRule", back_populates="policy_links"
    )

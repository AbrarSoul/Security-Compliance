"""Rename audit_logs actor_user_id and risk_level to user_id and severity

Revision ID: 009
Revises: 008
Create Date: 2026-05-18

"""

from typing import Sequence, Union

from alembic import op

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("audit_logs", "actor_user_id", new_column_name="user_id")
    op.alter_column("audit_logs", "risk_level", new_column_name="severity")

    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_risk_level", table_name="audit_logs")

    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"], unique=False)
    op.create_index(
        "ix_audit_logs_user_created",
        "audit_logs",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_audit_logs_severity"), "audit_logs", ["severity"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_severity"), table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_user_id"), table_name="audit_logs")

    op.create_index(
        "ix_audit_logs_risk_level", "audit_logs", ["risk_level"], unique=False
    )
    op.create_index(
        "ix_audit_logs_actor_created",
        "audit_logs",
        ["actor_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False
    )

    op.alter_column("audit_logs", "user_id", new_column_name="actor_user_id")
    op.alter_column("audit_logs", "severity", new_column_name="risk_level")

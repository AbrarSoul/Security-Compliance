"""Sprint 3 Step 5: compliance guard enforcement logs

Revision ID: 020
Revises: 019
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "020"
down_revision: Union[str, None] = "019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guard_enforcement_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "execution_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("execution_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitoring_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("enforcement_type", sa.String(32), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("action_taken", sa.String(32), nullable=False),
        sa.Column(
            "prompt_scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_scans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "output_scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("output_scans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reasons_json", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_guard_enforcement_logs_execution_request_id",
        "guard_enforcement_logs",
        ["execution_request_id"],
    )
    op.create_index("ix_guard_enforcement_logs_decision", "guard_enforcement_logs", ["decision"])


def downgrade() -> None:
    op.drop_index("ix_guard_enforcement_logs_decision", table_name="guard_enforcement_logs")
    op.drop_index(
        "ix_guard_enforcement_logs_execution_request_id",
        table_name="guard_enforcement_logs",
    )
    op.drop_table("guard_enforcement_logs")

"""Sprint 3 Step 4: output compliance scan persistence

Revision ID: 019
Revises: 018
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019"
down_revision: Union[str, None] = "018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "output_scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitoring_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "execution_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("execution_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "prompt_scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_scans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("output_hash", sa.String(64), nullable=False),
        sa.Column("content_length", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("findings_json", postgresql.JSONB(), nullable=True),
        sa.Column("masked_output", sa.Text(), nullable=True),
        sa.Column("redacted_output", sa.Text(), nullable=True),
        sa.Column("blocking_reasons_json", postgresql.JSONB(), nullable=True),
        sa.Column("warning_reasons_json", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations_json", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_output_scans_user_id", "output_scans", ["user_id"])
    op.create_index("ix_output_scans_session_id", "output_scans", ["session_id"])
    op.create_index("ix_output_scans_decision", "output_scans", ["decision"])
    op.create_index("ix_output_scans_scanned_at", "output_scans", ["scanned_at"])
    op.create_index("ix_output_scans_output_hash", "output_scans", ["output_hash"])


def downgrade() -> None:
    op.drop_index("ix_output_scans_output_hash", table_name="output_scans")
    op.drop_index("ix_output_scans_scanned_at", table_name="output_scans")
    op.drop_index("ix_output_scans_decision", table_name="output_scans")
    op.drop_index("ix_output_scans_session_id", table_name="output_scans")
    op.drop_index("ix_output_scans_user_id", table_name="output_scans")
    op.drop_table("output_scans")

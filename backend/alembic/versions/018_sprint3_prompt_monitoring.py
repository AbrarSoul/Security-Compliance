"""Sprint 3 Step 3: prompt scan persistence

Revision ID: 018
Revises: 017
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_scans",
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
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("content_length", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(16), nullable=False),
        sa.Column("findings_json", postgresql.JSONB(), nullable=True),
        sa.Column("masked_prompt", sa.Text(), nullable=True),
        sa.Column("blocking_reasons_json", postgresql.JSONB(), nullable=True),
        sa.Column("warning_reasons_json", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations_json", postgresql.JSONB(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_prompt_scans_user_id", "prompt_scans", ["user_id"])
    op.create_index("ix_prompt_scans_session_id", "prompt_scans", ["session_id"])
    op.create_index("ix_prompt_scans_decision", "prompt_scans", ["decision"])
    op.create_index("ix_prompt_scans_scanned_at", "prompt_scans", ["scanned_at"])
    op.create_index("ix_prompt_scans_prompt_hash", "prompt_scans", ["prompt_hash"])


def downgrade() -> None:
    op.drop_index("ix_prompt_scans_prompt_hash", table_name="prompt_scans")
    op.drop_index("ix_prompt_scans_scanned_at", table_name="prompt_scans")
    op.drop_index("ix_prompt_scans_decision", table_name="prompt_scans")
    op.drop_index("ix_prompt_scans_session_id", table_name="prompt_scans")
    op.drop_index("ix_prompt_scans_user_id", table_name="prompt_scans")
    op.drop_table("prompt_scans")

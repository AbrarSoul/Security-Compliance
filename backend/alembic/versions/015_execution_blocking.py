"""Execution blocking: acknowledgement and enforcement metadata

Revision ID: 015
Revises: 014
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "execution_requests",
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "execution_requests",
        sa.Column("acknowledged_by_user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "execution_requests",
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_execution_requests_acknowledged_by_user_id",
        "execution_requests",
        "users",
        ["acknowledged_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "execution_results",
        sa.Column(
            "blocking_reasons_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "execution_results",
        sa.Column(
            "warning_reasons_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "execution_results",
        sa.Column(
            "recommendations_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "execution_results",
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "execution_results",
        sa.Column("acknowledged_by_user_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_execution_results_acknowledged_by_user_id",
        "execution_results",
        "users",
        ["acknowledged_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_execution_results_acknowledged_by_user_id",
        "execution_results",
        type_="foreignkey",
    )
    op.drop_column("execution_results", "acknowledged_by_user_id")
    op.drop_column("execution_results", "acknowledged_at")
    op.drop_column("execution_results", "recommendations_json")
    op.drop_column("execution_results", "warning_reasons_json")
    op.drop_column("execution_results", "blocking_reasons_json")
    op.drop_constraint(
        "fk_execution_requests_acknowledged_by_user_id",
        "execution_requests",
        type_="foreignkey",
    )
    op.drop_column("execution_requests", "started_at")
    op.drop_column("execution_requests", "acknowledged_by_user_id")
    op.drop_column("execution_requests", "acknowledged_at")

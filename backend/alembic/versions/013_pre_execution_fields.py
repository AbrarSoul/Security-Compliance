"""Pre-execution: execution request fields and result risk level

Revision ID: 013
Revises: 012
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "execution_requests",
        sa.Column("compliance_model_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "execution_requests",
        sa.Column("execution_purpose", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_execution_requests_compliance_model_id",
        "execution_requests",
        "compliance_models",
        ["compliance_model_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_execution_requests_compliance_model_id"),
        "execution_requests",
        ["compliance_model_id"],
        unique=False,
    )

    op.add_column(
        "execution_results",
        sa.Column("risk_level", sa.String(length=16), nullable=True),
    )
    op.create_index(
        op.f("ix_execution_results_risk_level"),
        "execution_results",
        ["risk_level"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_execution_results_risk_level"), table_name="execution_results")
    op.drop_column("execution_results", "risk_level")
    op.drop_index(
        op.f("ix_execution_requests_compliance_model_id"), table_name="execution_requests"
    )
    op.drop_constraint(
        "fk_execution_requests_compliance_model_id", "execution_requests", type_="foreignkey"
    )
    op.drop_column("execution_requests", "execution_purpose")
    op.drop_column("execution_requests", "compliance_model_id")

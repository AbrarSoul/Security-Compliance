"""Policy status and priority columns

Revision ID: 011
Revises: 010
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "compliance_policies",
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
    )
    op.add_column(
        "compliance_policies",
        sa.Column("priority", sa.Integer(), server_default=sa.text("0"), nullable=False),
    )
    op.create_index(
        op.f("ix_compliance_policies_status"),
        "compliance_policies",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compliance_policies_priority"),
        "compliance_policies",
        ["priority"],
        unique=False,
    )

    op.execute(
        """
        UPDATE compliance_policies
        SET status = CASE WHEN is_active THEN 'active' ELSE 'inactive' END
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_compliance_policies_priority"), table_name="compliance_policies")
    op.drop_index(op.f("ix_compliance_policies_status"), table_name="compliance_policies")
    op.drop_column("compliance_policies", "priority")
    op.drop_column("compliance_policies", "status")

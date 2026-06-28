"""User registration approval workflow

Revision ID: 027
Revises: 026
Create Date: 2026-06-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "027"
down_revision: Union[str, None] = "026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "approval_status",
            sa.String(length=32),
            nullable=False,
            server_default="approved",
        ),
    )
    op.execute(
        """
        UPDATE users
        SET approval_status = 'approved'
        WHERE is_active = true
        """
    )
    op.execute(
        """
        UPDATE users
        SET approval_status = 'pending', is_active = false
        WHERE is_active = false
        """
    )
    op.create_index(
        op.f("ix_users_approval_status"),
        "users",
        ["approval_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_approval_status"), table_name="users")
    op.drop_column("users", "approval_status")

"""GAIRA AI application registration approval workflow

Revision ID: 028
Revises: 027
Create Date: 2026-06-29

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "028"
down_revision: Union[str, None] = "027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = (
    ("gaira:review", "Review pending AI application registrations"),
    ("gaira:approve", "Approve or reject AI application registrations"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": ("gaira:review", "gaira:approve"),
    "auditor": ("gaira:review",),
}


def upgrade() -> None:
    op.add_column(
        "ai_applications",
        sa.Column(
            "registration_status",
            sa.String(32),
            nullable=False,
            server_default="approved",
        ),
    )
    op.add_column("ai_applications", sa.Column("auditor_feedback", sa.Text(), nullable=True))
    op.add_column(
        "ai_applications",
        sa.Column(
            "auditor_reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_applications",
        sa.Column("auditor_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_applications",
        sa.Column(
            "approved_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_applications",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_applications",
        sa.Column(
            "rejected_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "ai_applications",
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("ai_applications", sa.Column("rejection_reason", sa.Text(), nullable=True))

    op.create_index(
        "ix_ai_applications_registration_status",
        "ai_applications",
        ["registration_status"],
    )

    for code, description in _NEW_PERMISSIONS:
        op.execute(
            sa.text(
                "INSERT INTO permissions (id, code, description) "
                "SELECT gen_random_uuid(), :code, :description "
                "WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = :code)"
            ).bindparams(code=code, description=description)
        )

    for role_name, perm_codes in _ROLE_PERMISSIONS.items():
        for perm_code in perm_codes:
            op.execute(
                sa.text(
                    "INSERT INTO role_permissions (role_id, permission_id) "
                    "SELECT r.id, p.id FROM roles r, permissions p "
                    "WHERE r.name = :role_name AND p.code = :perm_code "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM role_permissions rp "
                    "  JOIN roles rr ON rr.id = rp.role_id "
                    "  JOIN permissions pp ON pp.id = rp.permission_id "
                    "  WHERE rr.name = :role_name AND pp.code = :perm_code"
                    ")"
                ).bindparams(role_name=role_name, perm_code=perm_code)
            )


def downgrade() -> None:
    for role_name, perm_codes in _ROLE_PERMISSIONS.items():
        for perm_code in perm_codes:
            op.execute(
                sa.text(
                    "DELETE FROM role_permissions rp "
                    "USING roles r, permissions p "
                    "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
                    "AND r.name = :role_name AND p.code = :perm_code"
                ).bindparams(role_name=role_name, perm_code=perm_code)
            )

    for code, _ in _NEW_PERMISSIONS:
        op.execute(
            sa.text("DELETE FROM permissions WHERE code = :code").bindparams(code=code)
        )

    op.drop_index("ix_ai_applications_registration_status", table_name="ai_applications")
    op.drop_column("ai_applications", "rejection_reason")
    op.drop_column("ai_applications", "rejected_at")
    op.drop_column("ai_applications", "rejected_by_user_id")
    op.drop_column("ai_applications", "approved_at")
    op.drop_column("ai_applications", "approved_by_user_id")
    op.drop_column("ai_applications", "auditor_reviewed_at")
    op.drop_column("ai_applications", "auditor_reviewed_by_user_id")
    op.drop_column("ai_applications", "auditor_feedback")
    op.drop_column("ai_applications", "registration_status")

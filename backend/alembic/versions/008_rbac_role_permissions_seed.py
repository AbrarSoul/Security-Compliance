"""RBAC role_permissions table and seed permissions

Revision ID: 008
Revises: 007
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (code, description)
_PERMISSIONS = (
    ("file:upload", "Upload dataset files"),
    ("file:read", "Read own uploaded files"),
    ("scan:run", "Run compliance scans on own files"),
    ("scan:read", "View own scan results"),
    ("report:read", "View own compliance reports"),
    ("report:read_all", "View all users compliance reports"),
    ("execution:request", "Request pre-execution compliance validation"),
    ("user:manage", "Manage user accounts"),
    ("role:manage", "Manage roles and role assignments"),
    ("rule:manage", "Create and update compliance rules"),
    ("policy:manage", "Create and update compliance policies"),
    ("audit:read", "View audit logs"),
    ("policy_violation:read", "View policy violations and blocked executions"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": tuple(code for code, _ in _PERMISSIONS),
    "user": (
        "file:upload",
        "file:read",
        "scan:run",
        "scan:read",
        "report:read",
        "execution:request",
    ),
    "auditor": (
        "report:read_all",
        "audit:read",
        "policy_violation:read",
    ),
}


def upgrade() -> None:
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column("permission_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    for code, description in _PERMISSIONS:
        esc_desc = description.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO permissions (id, code, description, created_at)
            SELECT gen_random_uuid(), '{code}', '{esc_desc}', now()
            WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = '{code}')
            """
        )

    for role_name, codes in _ROLE_PERMISSIONS.items():
        codes_sql = ", ".join(f"'{c}'" for c in codes)
        op.execute(
            f"""
            INSERT INTO role_permissions (role_id, permission_id, created_at)
            SELECT r.id, p.id, now()
            FROM roles r
            CROSS JOIN permissions p
            WHERE r.name = '{role_name}'
              AND p.code IN ({codes_sql})
              AND NOT EXISTS (
                SELECT 1 FROM role_permissions rp
                WHERE rp.role_id = r.id AND rp.permission_id = p.id
              )
            """
        )

    # Existing accounts (pre-RBAC) receive the default User role
    op.execute(
        """
        INSERT INTO user_roles (id, user_id, role_id, created_at)
        SELECT gen_random_uuid(), u.id, r.id, now()
        FROM users u
        CROSS JOIN roles r
        WHERE r.name = 'user'
          AND NOT EXISTS (
            SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
          );
        """
    )


def downgrade() -> None:
    op.drop_table("role_permissions")

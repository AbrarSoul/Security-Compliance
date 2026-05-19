"""Sprint 3 Step 7: analytics dashboard permissions

Revision ID: 022
Revises: 021
Create Date: 2026-05-19

"""

from typing import Sequence, Union

from alembic import op

revision: str = "022"
down_revision: Union[str, None] = "021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = (
    ("analytics:read", "View own compliance analytics"),
    ("analytics:read_all", "View organization-wide analytics (admin/auditor)"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": ("analytics:read", "analytics:read_all"),
    "user": ("analytics:read",),
    "auditor": ("analytics:read", "analytics:read_all"),
}


def upgrade() -> None:
    for code, description in _NEW_PERMISSIONS:
        esc_desc = description.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO permissions (id, code, description, created_at)
            SELECT gen_random_uuid(), '{code}', '{esc_desc}', now()
            WHERE NOT EXISTS (SELECT 1 FROM permissions WHERE code = '{code}');
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
              );
            """
        )


def downgrade() -> None:
    for role_name, codes in _ROLE_PERMISSIONS.items():
        codes_sql = ", ".join(f"'{c}'" for c in codes)
        op.execute(
            f"""
            DELETE FROM role_permissions
            WHERE role_id IN (SELECT id FROM roles WHERE name = '{role_name}')
              AND permission_id IN (SELECT id FROM permissions WHERE code IN ({codes_sql}));
            """
        )
    for code, _ in _NEW_PERMISSIONS:
        op.execute(f"DELETE FROM permissions WHERE code = '{code}';")

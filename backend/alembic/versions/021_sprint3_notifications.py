"""Sprint 3 Step 6: notifications and preferences

Revision ID: 021
Revises: 020
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "021"
down_revision: Union[str, None] = "020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = (
    ("notification:read", "View own notifications"),
    ("notification:manage", "Manage notification preferences"),
    ("notification:read_all", "View all users notifications (admin)"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": ("notification:read", "notification:manage", "notification:read_all"),
    "user": ("notification:read", "notification:manage"),
    "auditor": ("notification:read", "notification:read_all"),
}


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notification_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(128), nullable=True),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_status", sa.String(32), nullable=True),
        sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_notification_type", "notifications", ["notification_type"])

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("email_min_severity", sa.String(16), nullable=False, server_default="high"),
        sa.Column("dashboard_alerts_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_prompt_blocked", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_output_blocked", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_policy_violation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_suspicious_activity", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_high_risk_execution", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_repeated_violation", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notify_system_security", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

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

    op.drop_table("notification_preferences")
    op.drop_index("ix_notifications_notification_type", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

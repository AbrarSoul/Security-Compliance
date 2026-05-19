"""Sprint 3: real-time monitoring pipeline tables and RBAC

Revision ID: 017
Revises: 016
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = (
    ("monitoring:read", "View monitoring sessions and events"),
    ("monitoring:read_all", "View all users monitoring sessions and events"),
    ("monitoring:publish", "Publish monitoring events"),
    ("monitoring:manage", "Open and close monitoring sessions"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": (
        "monitoring:read",
        "monitoring:read_all",
        "monitoring:publish",
        "monitoring:manage",
    ),
    "user": ("monitoring:read", "monitoring:publish", "monitoring:manage"),
    "auditor": ("monitoring:read", "monitoring:read_all"),
}


def upgrade() -> None:
    op.create_table(
        "monitoring_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "execution_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("execution_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("alert_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_risk_score", sa.Integer(), nullable=True),
        sa.Column("last_event_type", sa.String(128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_monitoring_sessions_user_id", "monitoring_sessions", ["user_id"])
    op.create_index("ix_monitoring_sessions_execution_request_id", "monitoring_sessions", ["execution_request_id"])
    op.create_index("ix_monitoring_sessions_status", "monitoring_sessions", ["status"])

    op.create_table(
        "domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitoring_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("severity", sa.String(16), nullable=False, server_default="info"),
        sa.Column("source", sa.String(32), nullable=False, server_default="api"),
        sa.Column("payload_json", postgresql.JSONB(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_domain_events_event_type", "domain_events", ["event_type"])
    op.create_index("ix_domain_events_user_id", "domain_events", ["user_id"])
    op.create_index("ix_domain_events_session_id", "domain_events", ["session_id"])
    op.create_index("ix_domain_events_occurred_at", "domain_events", ["occurred_at"])

    op.create_table(
        "event_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "domain_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("domain_events.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_event_outbox_status", "event_outbox", ["status"])
    op.create_index("ix_event_outbox_event_type", "event_outbox", ["event_type"])

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
              AND permission_id IN (
                SELECT id FROM permissions WHERE code IN ({codes_sql})
              );
            """
        )
    for code, _ in _NEW_PERMISSIONS:
        op.execute(f"DELETE FROM permissions WHERE code = '{code}';")

    op.drop_index("ix_event_outbox_event_type", table_name="event_outbox")
    op.drop_index("ix_event_outbox_status", table_name="event_outbox")
    op.drop_table("event_outbox")

    op.drop_index("ix_domain_events_occurred_at", table_name="domain_events")
    op.drop_index("ix_domain_events_session_id", table_name="domain_events")
    op.drop_index("ix_domain_events_user_id", table_name="domain_events")
    op.drop_index("ix_domain_events_event_type", table_name="domain_events")
    op.drop_table("domain_events")

    op.drop_index("ix_monitoring_sessions_status", table_name="monitoring_sessions")
    op.drop_index("ix_monitoring_sessions_execution_request_id", table_name="monitoring_sessions")
    op.drop_index("ix_monitoring_sessions_user_id", table_name="monitoring_sessions")
    op.drop_table("monitoring_sessions")

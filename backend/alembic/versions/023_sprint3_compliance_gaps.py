"""Sprint 3 Step 8: compliance gap analysis

Revision ID: 023
Revises: 022
Create Date: 2026-05-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "023"
down_revision: Union[str, None] = "022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = (
    ("gap:read", "View compliance gaps"),
    ("gap:analyze", "Run compliance gap analysis"),
    ("gap:read_all", "View organization-wide compliance gaps"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": ("gap:read", "gap:analyze", "gap:read_all"),
    "user": ("gap:read",),
    "auditor": ("gap:read", "gap:read_all"),
}


def upgrade() -> None:
    op.create_table(
        "gap_analysis_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("triggered_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("scope", sa.String(32), nullable=False, server_default="organization"),
        sa.Column("gaps_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("critical_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("high_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("medium_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary_json", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "compliance_gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("analysis_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("gap_analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gap_type", sa.String(64), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("fingerprint", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_compliance_gaps_analysis_run_id", "compliance_gaps", ["analysis_run_id"])
    op.create_index("ix_compliance_gaps_gap_type", "compliance_gaps", ["gap_type"])
    op.create_index("ix_compliance_gaps_severity", "compliance_gaps", ["severity"])
    op.create_index("ix_compliance_gaps_status", "compliance_gaps", ["status"])
    op.create_index("ix_compliance_gaps_fingerprint", "compliance_gaps", ["fingerprint"])

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

    op.drop_index("ix_compliance_gaps_fingerprint", table_name="compliance_gaps")
    op.drop_index("ix_compliance_gaps_status", table_name="compliance_gaps")
    op.drop_index("ix_compliance_gaps_severity", table_name="compliance_gaps")
    op.drop_index("ix_compliance_gaps_gap_type", table_name="compliance_gaps")
    op.drop_index("ix_compliance_gaps_analysis_run_id", table_name="compliance_gaps")
    op.drop_table("compliance_gaps")
    op.drop_table("gap_analysis_runs")

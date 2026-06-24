"""Sprint 4: GAIRA AI risk assessment tables

Revision ID: 026
Revises: 025
Create Date: 2026-06-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "026"
down_revision: Union[str, None] = "025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = (
    ("gaira:read", "View GAIRA framework and assessments"),
    ("gaira:manage", "Create and submit GAIRA assessments"),
    ("gaira:read_all", "View organization-wide GAIRA records"),
)

_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "admin": ("gaira:read", "gaira:manage", "gaira:read_all"),
    "user": ("gaira:read", "gaira:manage"),
    "auditor": ("gaira:read", "gaira:read_all"),
}


def upgrade() -> None:
    op.create_table(
        "ai_applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(128), nullable=True, unique=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("owner_name", sa.String(255), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("audience", sa.String(255), nullable=True),
        sa.Column("scope_includes", sa.Text(), nullable=True),
        sa.Column("scope_excludes", sa.Text(), nullable=True),
        sa.Column("technology_description", sa.Text(), nullable=True),
        sa.Column("ai_provider", sa.String(255), nullable=True),
        sa.Column(
            "compliance_model_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("compliance_models.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ai_act_category", sa.String(64), nullable=True),
        sa.Column("risk_level", sa.String(32), nullable=True),
        sa.Column("gaira_status", sa.String(32), nullable=False, server_default="none"),
        sa.Column("compliance_check_status", sa.String(32), nullable=False, server_default="none"),
        sa.Column("dpia_status", sa.String(32), nullable=False, server_default="none"),
        sa.Column("deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_assessment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_ai_applications_name", "ai_applications", ["name"])
    op.create_index("ix_ai_applications_code", "ai_applications", ["code"])
    op.create_index("ix_ai_applications_compliance_model_id", "ai_applications", ["compliance_model_id"])
    op.create_index("ix_ai_applications_risk_level", "ai_applications", ["risk_level"])
    op.create_index("ix_ai_applications_gaira_status", "ai_applications", ["gaira_status"])
    op.create_index("ix_ai_applications_is_active", "ai_applications", ["is_active"])

    op.create_table(
        "gaira_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "application_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assessment_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("framework_version", sa.String(64), nullable=True),
        sa.Column("current_step", sa.String(16), nullable=True),
        sa.Column("answers_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("computed_json", postgresql.JSONB(), nullable=True),
        sa.Column("overall_risk_level", sa.String(32), nullable=True),
        sa.Column("proceed_decision", sa.String(64), nullable=True),
        sa.Column("decision_comments", sa.Text(), nullable=True),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "decision_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_gaira_assessments_application_id", "gaira_assessments", ["application_id"])
    op.create_index("ix_gaira_assessments_assessment_type", "gaira_assessments", ["assessment_type"])
    op.create_index("ix_gaira_assessments_status", "gaira_assessments", ["status"])

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

    op.drop_index("ix_gaira_assessments_status", table_name="gaira_assessments")
    op.drop_index("ix_gaira_assessments_assessment_type", table_name="gaira_assessments")
    op.drop_index("ix_gaira_assessments_application_id", table_name="gaira_assessments")
    op.drop_table("gaira_assessments")

    op.drop_index("ix_ai_applications_is_active", table_name="ai_applications")
    op.drop_index("ix_ai_applications_gaira_status", table_name="ai_applications")
    op.drop_index("ix_ai_applications_risk_level", table_name="ai_applications")
    op.drop_index("ix_ai_applications_compliance_model_id", table_name="ai_applications")
    op.drop_index("ix_ai_applications_code", table_name="ai_applications")
    op.drop_index("ix_ai_applications_name", table_name="ai_applications")
    op.drop_table("ai_applications")

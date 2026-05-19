"""Sprint 2: roles, permissions, policies, rules, audit, execution workflow tables

Revision ID: 007
Revises: 006
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "compliance_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("policy_type", sa.String(length=32), nullable=False),
        sa.Column(
            "definition_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("severity_default", sa.String(length=16), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_compliance_policies_is_active"), "compliance_policies", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_compliance_policies_policy_type"),
        "compliance_policies",
        ["policy_type"],
        unique=False,
    )

    op.create_table(
        "compliance_rules",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("condition_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by_user_id", sa.UUID(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(
        op.f("ix_compliance_rules_action"), "compliance_rules", ["action"], unique=False
    )
    op.create_index(
        op.f("ix_compliance_rules_category"), "compliance_rules", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_compliance_rules_is_enabled"), "compliance_rules", ["is_enabled"], unique=False
    )
    op.create_index(
        op.f("ix_compliance_rules_severity"), "compliance_rules", ["severity"], unique=False
    )

    op.create_table(
        "policy_rules",
        sa.Column("policy_id", sa.UUID(), nullable=False),
        sa.Column("rule_id", sa.UUID(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["policy_id"], ["compliance_policies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rule_id"], ["compliance_rules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("policy_id", "rule_id"),
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role_id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
    )
    op.create_index(op.f("ix_user_roles_role_id"), "user_roles", ["role_id"], unique=False)
    op.create_index(op.f("ix_user_roles_user_id"), "user_roles", ["user_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.UUID(), nullable=True),
        sa.Column("risk_level", sa.String(length=16), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_request_id"), "audit_logs", ["request_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)
    op.create_index(
        op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False
    )
    op.create_index(op.f("ix_audit_logs_risk_level"), "audit_logs", ["risk_level"], unique=False)
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"], unique=False)
    op.create_index(
        "ix_audit_logs_resource_type_resource_id",
        "audit_logs",
        ["resource_type", "resource_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_logs_actor_created",
        "audit_logs",
        ["actor_user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "execution_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=True),
        sa.Column("model_provider", sa.String(length=255), nullable=True),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("model_endpoint_url", sa.Text(), nullable=True),
        sa.Column("is_external_api", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_execution_requests_file_id"), "execution_requests", ["file_id"], unique=False
    )
    op.create_index(
        op.f("ix_execution_requests_scan_id"), "execution_requests", ["scan_id"], unique=False
    )
    op.create_index(
        op.f("ix_execution_requests_status"), "execution_requests", ["status"], unique=False
    )
    op.create_index(
        op.f("ix_execution_requests_user_id"), "execution_requests", ["user_id"], unique=False
    )
    op.create_index(
        "ix_execution_requests_user_status",
        "execution_requests",
        ["user_id", "status"],
        unique=False,
    )

    op.create_table(
        "model_validations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_request_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("risk_score", sa.SmallInteger(), nullable=True),
        sa.Column("flags_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("details_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_request_id"], ["execution_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_request_id"),
    )
    op.create_index(
        op.f("ix_model_validations_status"), "model_validations", ["status"], unique=False
    )

    op.create_table(
        "execution_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_request_id", sa.UUID(), nullable=False),
        sa.Column("decision", sa.String(length=16), nullable=True),
        sa.Column("risk_score", sa.SmallInteger(), nullable=True),
        sa.Column(
            "reason_codes_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("evaluation_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'pending'"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["execution_request_id"], ["execution_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_request_id"),
    )
    op.create_index(
        op.f("ix_execution_results_decision"), "execution_results", ["decision"], unique=False
    )
    op.create_index(
        op.f("ix_execution_results_status"), "execution_results", ["status"], unique=False
    )

    # Seed system roles (idempotent on name; one statement per execute for asyncpg)
    _SEED_ROLES = (
        ("admin", "Admin", "Full system administration and policy management."),
        ("user", "User", "Standard user: upload datasets and run scans / validations."),
        ("auditor", "Auditor", "Read-only access to reports and audit logs."),
    )
    for name, display_name, description in _SEED_ROLES:
        esc_display = display_name.replace("'", "''")
        esc_desc = description.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO roles (id, name, display_name, description, is_system, created_at, updated_at)
            SELECT gen_random_uuid(), '{name}', '{esc_display}',
                   '{esc_desc}', true, now(), now()
            WHERE NOT EXISTS (SELECT 1 FROM roles WHERE name = '{name}')
            """
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_execution_results_status"), table_name="execution_results")
    op.drop_index(op.f("ix_execution_results_decision"), table_name="execution_results")
    op.drop_table("execution_results")

    op.drop_index(op.f("ix_model_validations_status"), table_name="model_validations")
    op.drop_table("model_validations")

    op.drop_index("ix_execution_requests_user_status", table_name="execution_requests")
    op.drop_index(op.f("ix_execution_requests_user_id"), table_name="execution_requests")
    op.drop_index(op.f("ix_execution_requests_status"), table_name="execution_requests")
    op.drop_index(op.f("ix_execution_requests_scan_id"), table_name="execution_requests")
    op.drop_index(op.f("ix_execution_requests_file_id"), table_name="execution_requests")
    op.drop_table("execution_requests")

    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_type_resource_id", table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_status"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_risk_level"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_request_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_user_roles_user_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_role_id"), table_name="user_roles")
    op.drop_table("user_roles")

    op.drop_table("policy_rules")

    op.drop_index(op.f("ix_compliance_rules_severity"), table_name="compliance_rules")
    op.drop_index(op.f("ix_compliance_rules_is_enabled"), table_name="compliance_rules")
    op.drop_index(op.f("ix_compliance_rules_category"), table_name="compliance_rules")
    op.drop_index(op.f("ix_compliance_rules_action"), table_name="compliance_rules")
    op.drop_table("compliance_rules")

    op.drop_index(op.f("ix_compliance_policies_policy_type"), table_name="compliance_policies")
    op.drop_index(op.f("ix_compliance_policies_is_active"), table_name="compliance_policies")
    op.drop_table("compliance_policies")

    op.drop_table("permissions")

    op.drop_table("roles")

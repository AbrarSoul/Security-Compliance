"""Sprint 2 Step 6: compliance model registry and standalone model validations

Revision ID: 012
Revises: 011
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compliance_models",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=255), nullable=True),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("endpoint_url", sa.Text(), nullable=True),
        sa.Column("data_retention_policy", sa.Text(), nullable=True),
        sa.Column("logging_enabled", sa.Boolean(), nullable=True),
        sa.Column(
            "data_leaves_platform",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_approved",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
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
        op.f("ix_compliance_models_is_active"), "compliance_models", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_compliance_models_is_approved"),
        "compliance_models",
        ["is_approved"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compliance_models_model_type"),
        "compliance_models",
        ["model_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compliance_models_provider"), "compliance_models", ["provider"], unique=False
    )

    op.alter_column(
        "model_validations",
        "execution_request_id",
        existing_type=sa.UUID(),
        nullable=True,
    )

    op.add_column(
        "model_validations",
        sa.Column("user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "model_validations",
        sa.Column("scan_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "model_validations",
        sa.Column("compliance_model_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "model_validations",
        sa.Column("decision", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "model_validations",
        sa.Column("risk_level", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "model_validations",
        sa.Column("primary_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "model_validations",
        sa.Column("recommendations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_foreign_key(
        "fk_model_validations_user_id",
        "model_validations",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_model_validations_scan_id",
        "model_validations",
        "scans",
        ["scan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_model_validations_compliance_model_id",
        "model_validations",
        "compliance_models",
        ["compliance_model_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_model_validations_scan_id"), "model_validations", ["scan_id"], unique=False
    )
    op.create_index(
        op.f("ix_model_validations_compliance_model_id"),
        "model_validations",
        ["compliance_model_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_model_validations_decision"), "model_validations", ["decision"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_model_validations_decision"), table_name="model_validations")
    op.drop_index(
        op.f("ix_model_validations_compliance_model_id"), table_name="model_validations"
    )
    op.drop_index(op.f("ix_model_validations_scan_id"), table_name="model_validations")
    op.drop_constraint(
        "fk_model_validations_compliance_model_id", "model_validations", type_="foreignkey"
    )
    op.drop_constraint("fk_model_validations_scan_id", "model_validations", type_="foreignkey")
    op.drop_constraint("fk_model_validations_user_id", "model_validations", type_="foreignkey")
    op.drop_column("model_validations", "recommendations_json")
    op.drop_column("model_validations", "primary_reason")
    op.drop_column("model_validations", "risk_level")
    op.drop_column("model_validations", "decision")
    op.drop_column("model_validations", "compliance_model_id")
    op.drop_column("model_validations", "scan_id")
    op.drop_column("model_validations", "user_id")
    op.alter_column(
        "model_validations",
        "execution_request_id",
        existing_type=sa.UUID(),
        nullable=False,
    )
    op.drop_table("compliance_models")

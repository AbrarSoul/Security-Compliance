"""Sprint 2 Step 4: scan rule evaluation storage and seed compliance rules

Revision ID: 010
Revises: 009
Create Date: 2026-05-18

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SEED_RULES = (
    (
        "a1000001-0001-4001-8001-000000000001",
        "data.email_detected",
        "Email detected",
        "Dataset contains email addresses",
        "data",
        "medium",
        50,
        '{"field": "detected_types", "operator": "contains", "value": "email"}',
        "warn",
    ),
    (
        "a1000001-0001-4001-8001-000000000002",
        "data.password_detected",
        "Password detected",
        "Dataset contains password-like values",
        "data",
        "critical",
        90,
        '{"field": "detected_types", "operator": "contains", "value": "password"}',
        "block",
    ),
    (
        "a1000001-0001-4001-8001-000000000003",
        "data.api_key_detected",
        "API key detected",
        "Dataset contains API key patterns",
        "security",
        "critical",
        95,
        '{"field": "detected_types", "operator": "contains", "value": "api_key"}',
        "block",
    ),
    (
        "a1000001-0001-4001-8001-000000000004",
        "model.sensitive_data_external",
        "Sensitive data with external model",
        "Sensitive data must not be sent to external models",
        "model",
        "critical",
        100,
        """
        {"all": [
          {"any": [
            {"field": "detected_types", "operator": "contains", "value": "password"},
            {"field": "detected_types", "operator": "contains", "value": "api_key"},
            {"field": "detected_types", "operator": "contains", "value": "sensitive_field"}
          ]},
          {"field": "model.is_external", "operator": "equals", "value": true}
        ]}
        """.strip(),
        "block",
    ),
    (
        "a1000001-0001-4001-8001-000000000005",
        "model.confidential_data_cloud",
        "Confidential data with cloud model",
        "Confidential or restricted data with cloud-hosted models requires review",
        "privacy",
        "high",
        80,
        """
        {"all": [
          {"field": "classification", "operator": "in", "value": ["confidential", "restricted"]},
          {"field": "model.deployment", "operator": "equals", "value": "cloud"}
        ]}
        """.strip(),
        "warn",
    ),
)


def upgrade() -> None:
    op.add_column(
        "scans",
        sa.Column("rule_evaluation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    for (
        rule_id,
        code,
        name,
        description,
        category,
        severity,
        priority,
        condition_json,
        action,
    ) in _SEED_RULES:
        esc_desc = description.replace("'", "''")
        esc_name = name.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO compliance_rules (
                id, code, name, description, category, severity, priority,
                condition_json, action, is_enabled, created_at, updated_at
            )
            SELECT
                '{rule_id}'::uuid,
                '{code}',
                '{esc_name}',
                '{esc_desc}',
                '{category}',
                '{severity}',
                {priority},
                '{condition_json}'::jsonb,
                '{action}',
                true,
                now(),
                now()
            WHERE NOT EXISTS (SELECT 1 FROM compliance_rules WHERE code = '{code}')
            """
        )


def downgrade() -> None:
    for _, code, *_ in _SEED_RULES:
        op.execute(f"DELETE FROM compliance_rules WHERE code = '{code}'")
    op.drop_column("scans", "rule_evaluation_json")

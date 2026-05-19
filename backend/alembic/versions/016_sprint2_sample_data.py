"""Sprint 2 Step 10: sample policies, models, and demo workflow links

Revision ID: 016
Revises: 015
Create Date: 2026-05-18

Seeds three example compliance models and two active policies with rule links
for end-to-end workflow demonstrations (safe local, warning, blocked external).
"""

from typing import Sequence, Union

from alembic import op

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Demo models
_MODELS = (
    (
        "b2000001-0001-4001-8001-000000000001",
        "DEMO_LOCAL_LLM",
        "Demo Local LLM",
        "Internal",
        "local_model",
        False,
        True,
        True,
    ),
    (
        "b2000001-0001-4001-8001-000000000002",
        "DEMO_EXTERNAL_API",
        "Demo External API (GPT)",
        "OpenAI",
        "external_api",
        True,
        False,
        True,
    ),
    (
        "b2000001-0001-4001-8001-000000000003",
        "DEMO_CLOUD_UNAPPROVED",
        "Demo Cloud Model (Unapproved)",
        "CloudVendor",
        "cloud_hosted",
        True,
        False,
        False,
    ),
)

# Demo policies (status active, thresholds in definition_json)
_POLICIES = (
    (
        "c2000001-0001-4001-8001-000000000001",
        "Demo Execution Baseline",
        "Baseline execution policy for Sprint 2 demos",
        "execution_policy",
        "active",
        10,
        '{"thresholds": {"block_below": 40, "warn_below": 70}}',
    ),
    (
        "c2000001-0001-4001-8001-000000000002",
        "Demo Data Protection",
        "Blocks high-risk sensitive data combinations",
        "data_policy",
        "active",
        20,
        '{"thresholds": {"block_below": 35, "warn_below": 65}}',
    ),
)

# policy_id -> list of rule_ids from migration 010
_POLICY_RULES = (
    ("c2000001-0001-4001-8001-000000000001", "a1000001-0001-4001-8001-000000000001", 0),
    ("c2000001-0001-4001-8001-000000000001", "a1000001-0001-4001-8001-000000000005", 10),
    ("c2000001-0001-4001-8001-000000000002", "a1000001-0001-4001-8001-000000000002", 0),
    ("c2000001-0001-4001-8001-000000000002", "a1000001-0001-4001-8001-000000000003", 10),
    ("c2000001-0001-4001-8001-000000000002", "a1000001-0001-4001-8001-000000000004", 20),
)


def upgrade() -> None:
    for (
        model_id,
        code,
        name,
        provider,
        model_type,
        data_leaves,
        is_approved,
        is_active,
    ) in _MODELS:
        esc_name = name.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO compliance_models (
                id, code, name, provider, model_type, endpoint_url,
                data_retention_policy, logging_enabled, data_leaves_platform,
                is_approved, is_active, metadata_json, created_at, updated_at
            )
            SELECT
                '{model_id}'::uuid, '{code}', '{esc_name}', '{provider}', '{model_type}',
                NULL, 'demo retention policy', false, {str(data_leaves).lower()},
                {str(is_approved).lower()}, {str(is_active).lower()}, '{{}}'::jsonb,
                NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM compliance_models WHERE code = '{code}')
            """
        )

    for policy_id, name, description, policy_type, status, priority, definition in _POLICIES:
        esc_name = name.replace("'", "''")
        esc_desc = description.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO compliance_policies (
                id, name, description, policy_type, status, priority,
                definition_json, is_active, severity_default,
                created_at, updated_at
            )
            SELECT
                '{policy_id}'::uuid, '{esc_name}', '{esc_desc}', '{policy_type}',
                '{status}', {priority}, '{definition}'::jsonb, true, 'medium',
                NOW(), NOW()
            WHERE NOT EXISTS (SELECT 1 FROM compliance_policies WHERE id = '{policy_id}'::uuid)
            """
        )

    for policy_id, rule_id, sort_order in _POLICY_RULES:
        op.execute(
            f"""
            INSERT INTO policy_rules (policy_id, rule_id, sort_order)
            SELECT '{policy_id}'::uuid, '{rule_id}'::uuid, {sort_order}
            WHERE NOT EXISTS (
                SELECT 1 FROM policy_rules
                WHERE policy_id = '{policy_id}'::uuid AND rule_id = '{rule_id}'::uuid
            )
            """
        )


def downgrade() -> None:
    for policy_id, rule_id, _ in _POLICY_RULES:
        op.execute(
            f"DELETE FROM policy_rules WHERE policy_id = '{policy_id}'::uuid "
            f"AND rule_id = '{rule_id}'::uuid"
        )
    for policy_id, *_ in _POLICIES:
        op.execute(f"DELETE FROM compliance_policies WHERE id = '{policy_id}'::uuid")
    for model_id, code, *_ in _MODELS:
        op.execute(f"DELETE FROM compliance_models WHERE code = '{code}'")

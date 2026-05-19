"""Unit tests for policy schema validation and response mapping."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.compliance_policy import CompliancePolicy
from app.schemas.policies import CompliancePolicyCreate, PolicyThresholdsSchema
from app.services.policy_service import PolicyService


def test_thresholds_validation_warn_above_block():
    with pytest.raises(ValueError):
        PolicyThresholdsSchema(block_below=70, warn_below=40)


def test_policy_create_schema_defaults():
    payload = CompliancePolicyCreate(
        name="Test Policy",
        policy_type="execution_policy",
    )
    assert payload.status == "draft"
    assert payload.thresholds.block_below == 40
    assert payload.thresholds.warn_below == 70


def test_policy_response_from_model():
    policy = CompliancePolicy(
        id=uuid.uuid4(),
        name="External Model Sensitive Data Policy",
        description="Test",
        policy_type="execution_policy",
        status="active",
        priority=20,
        definition_json={"thresholds": {"block_below": 40, "warn_below": 70}},
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    policy.policy_rule_links = []

    response = PolicyService.to_policy_response(policy)
    assert response.name == "External Model Sensitive Data Policy"
    assert response.policy_type == "execution_policy"
    assert response.status == "active"
    assert response.thresholds.warn_below == 70

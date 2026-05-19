"""Unit tests for model compliance checker and risk checks."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.compliance_model import ComplianceModel
from app.services.model_compliance.checker import ModelComplianceChecker
from app.services.model_compliance.checks import run_model_risk_checks
from app.services.model_compliance.types import DatasetContext, ModelContext
from app.services.policies.thresholds import PolicyThresholdConfig, action_from_validation_score


def _compliance_model(**kwargs) -> ComplianceModel:
    defaults = {
        "id": uuid.uuid4(),
        "code": "openai-gpt4",
        "name": "GPT-4",
        "provider": "OpenAI",
        "model_type": "external_api",
        "endpoint_url": "https://api.openai.com/v1/chat/completions",
        "data_retention_policy": "May retain prompts for 30 days",
        "logging_enabled": True,
        "data_leaves_platform": True,
        "is_approved": False,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return ComplianceModel(**defaults)


class TestModelRiskChecks:
    def test_external_api_with_sensitive_data(self):
        dataset = DatasetContext(
            detected_types={"email", "sensitive_field"},
            classification="confidential",
        )
        model = ModelContext(
            name="GPT-4",
            provider="OpenAI",
            model_type="external_api",
            data_leaves_platform=True,
            logging_enabled=True,
            is_approved=False,
        )
        checks = run_model_risk_checks(dataset, model)
        codes = {c.code for c in checks}
        assert "external_api_sensitive_data" in codes
        assert "confidential_data_external" in codes
        assert "unapproved_endpoint" in codes

    def test_cloud_with_restricted_classification(self):
        dataset = DatasetContext(
            detected_types={"phone"},
            classification="restricted",
        )
        model = ModelContext(
            name="Cloud LLM",
            provider="Vendor",
            model_type="cloud_hosted",
            data_leaves_platform=True,
            is_approved=True,
        )
        checks = run_model_risk_checks(dataset, model)
        assert any(c.code == "cloud_restricted_data" for c in checks)

    def test_local_model_low_risk(self):
        dataset = DatasetContext(detected_types={"email"}, classification="internal")
        model = ModelContext(
            name="Local LLM",
            provider="Internal",
            model_type="local_model",
            data_leaves_platform=False,
            is_approved=True,
            logging_enabled=False,
        )
        checks = run_model_risk_checks(dataset, model)
        assert checks == []


class TestModelComplianceChecker:
    def test_confidential_external_openai_example(self):
        model = _compliance_model(
            name="GPT-4 External",
            provider="OpenAI",
            model_type="external_api",
            data_leaves_platform=True,
            is_approved=False,
        )
        dataset = DatasetContext(
            detected_types={"email", "sensitive_field"},
            classification="confidential",
            risk_score=55,
        )
        checker = ModelComplianceChecker()
        result = checker.check(dataset, model)

        assert result.decision in ("warn", "block")
        assert result.risk_level in ("high", "critical")
        assert "external" in result.primary_reason.lower() or "confidential" in result.primary_reason.lower()
        assert any("anonymize" in r.lower() or "local" in r.lower() for r in result.recommendations)

    def test_approved_local_model_allow(self):
        model = _compliance_model(
            code="local-llm",
            name="On-Prem LLM",
            provider="Internal",
            model_type="local_model",
            data_leaves_platform=False,
            logging_enabled=False,
            is_approved=True,
            data_retention_policy="No retention",
        )
        dataset = DatasetContext(detected_types={"email"}, classification="internal", risk_score=20)
        result = ModelComplianceChecker().check(dataset, model)

        assert result.decision == "allow"
        assert result.risk_level == "low"

    def test_unknown_provider_warns(self):
        model = _compliance_model(provider=None, model_type="proprietary", is_approved=True)
        dataset = DatasetContext(detected_types=set(), classification="public")
        checks = run_model_risk_checks(
            dataset,
            ModelContext(
                name=model.name,
                provider=model.provider,
                model_type=model.model_type,
                is_approved=True,
            ),
        )
        assert any(c.code == "unknown_provider" for c in checks)


class TestThresholds:
    def test_policy_threshold_bands(self):
        thresholds = PolicyThresholdConfig(block_below=40, warn_below=70)
        assert action_from_validation_score(30, thresholds) == "block"
        assert action_from_validation_score(50, thresholds) == "warn"
        assert action_from_validation_score(80, thresholds) == "allow"

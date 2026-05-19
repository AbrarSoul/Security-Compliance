"""Unit tests for pre-execution validation aggregation and risk scenarios."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.compliance_model import ComplianceModel
from app.services.execution.pre_execution_validator import PreExecutionValidator
from app.services.model_compliance import DatasetContext
from app.services.model_compliance.checker import ModelComplianceChecker
from app.services.model_compliance.types import ModelComplianceCheckResult
from app.services.policies.types import PoliciesEvaluationResult, PolicyEvaluationResult
from app.services.rules.types import RuleEvaluationResult, TriggeredRule


def _model(**kwargs) -> ComplianceModel:
    defaults = {
        "id": uuid.uuid4(),
        "code": "test-model",
        "name": "Test Model",
        "provider": "Internal",
        "model_type": "local_model",
        "endpoint_url": None,
        "data_retention_policy": "No retention",
        "logging_enabled": False,
        "data_leaves_platform": False,
        "is_approved": True,
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return ComplianceModel(**defaults)


def _empty_rule_result() -> RuleEvaluationResult:
    return RuleEvaluationResult(
        triggered_rules=[],
        rules_evaluated=0,
        aggregated_risk_score=0,
        aggregated_severity=None,
        recommended_action="allow",
        decision_reason="No rules triggered",
    )


def _empty_policy_result() -> PoliciesEvaluationResult:
    return PoliciesEvaluationResult(
        policy_results=[],
        policies_evaluated=0,
        recommended_action="allow",
        decision_reason="No active policies evaluated",
    )


class TestPreExecutionValidator:
    def test_safe_dataset_local_model_allow(self):
        dataset = DatasetContext(detected_types={"email"}, classification="internal")
        model = _model(model_type="local_model", provider="Internal", is_approved=True)
        model_result = ModelComplianceChecker().check(dataset, model)

        outcome = PreExecutionValidator().aggregate(
            scan_risk_score=15,
            scan_classification="internal",
            rule_result=_empty_rule_result(),
            policy_result=_empty_policy_result(),
            model_result=model_result,
        )

        assert outcome.decision == "allow"
        assert outcome.risk_level == "low"

    def test_sensitive_external_warn_or_block(self):
        dataset = DatasetContext(
            detected_types={"email", "sensitive_field"},
            classification="confidential",
            risk_score=55,
        )
        model = _model(
            name="GPT-4",
            provider="OpenAI",
            model_type="external_api",
            data_leaves_platform=True,
            logging_enabled=True,
            is_approved=False,
        )
        model_result = ModelComplianceChecker().check(dataset, model)

        outcome = PreExecutionValidator().aggregate(
            scan_risk_score=55,
            scan_classification="confidential",
            rule_result=_empty_rule_result(),
            policy_result=_empty_policy_result(),
            model_result=model_result,
        )

        assert outcome.decision in ("warn", "block")
        assert outcome.risk_level in ("high", "critical")
        assert any("anonymize" in r.lower() or "local" in r.lower() for r in outcome.recommendations)

    def test_password_external_block(self):
        dataset = DatasetContext(
            detected_types={"password"},
            classification="restricted",
            risk_score=80,
        )
        model = _model(
            provider="OpenAI",
            model_type="external_api",
            data_leaves_platform=True,
            is_approved=False,
        )
        rule_result = RuleEvaluationResult(
            triggered_rules=[
                TriggeredRule(
                    rule_id=uuid.uuid4(),
                    rule_name="Password detected",
                    rule_code="data.password_detected",
                    category="data",
                    severity="critical",
                    action="block",
                    priority=90,
                    reason="Dataset contains password-like values",
                )
            ],
            rules_evaluated=1,
            aggregated_risk_score=50,
            aggregated_severity="critical",
            recommended_action="block",
            decision_reason="Blocked by rule: Password detected",
        )
        model_result = ModelComplianceCheckResult(
            decision="block",
            risk_level="critical",
            risk_score=60,
            primary_reason="External API with sensitive data",
            recommendations=["Use a local model"],
        )
        model_result.risk_checks = ModelComplianceChecker().check(dataset, model).risk_checks

        outcome = PreExecutionValidator().aggregate(
            scan_risk_score=80,
            scan_classification="restricted",
            rule_result=rule_result,
            policy_result=_empty_policy_result(),
            model_result=model_result,
        )

        assert outcome.decision == "block"
        assert any(t["rule_code"] == "data.password_detected" for t in outcome.triggered_rules)

    def test_unknown_provider_warn(self):
        dataset = DatasetContext(detected_types=set(), classification="public")
        model = _model(provider=None, model_type="proprietary", is_approved=True)
        model_result = ModelComplianceChecker().check(dataset, model)

        outcome = PreExecutionValidator().aggregate(
            scan_risk_score=5,
            scan_classification="public",
            rule_result=_empty_rule_result(),
            policy_result=_empty_policy_result(),
            model_result=model_result,
        )

        assert outcome.decision in ("warn", "allow")
        if outcome.decision == "warn":
            assert any(r["code"] == "unknown_provider" for r in outcome.model_risks)

    def test_policy_violation_extracted(self):
        policy_id = uuid.uuid4()
        policy_result = PoliciesEvaluationResult(
            policy_results=[
                PolicyEvaluationResult(
                    policy_id=policy_id,
                    policy_name="Test Policy",
                    policy_type="execution_policy",
                    status="active",
                    priority=10,
                    validation_score=50,
                    threshold_action="warn",
                    rule_evaluation=_empty_rule_result(),
                    recommended_action="warn",
                    decision_reason="Policy threshold warning",
                )
            ],
            policies_evaluated=1,
            recommended_action="warn",
            decision_reason="Policy threshold warning",
        )
        outcome = PreExecutionValidator().aggregate(
            scan_risk_score=50,
            scan_classification="confidential",
            rule_result=_empty_rule_result(),
            policy_result=policy_result,
            model_result=ModelComplianceCheckResult(),
        )
        assert len(outcome.policy_violations) == 1
        assert outcome.policy_violations[0].action == "warn"


class TestValidateExecutionRequestSchema:
    def test_execution_purpose_required(self):
        from pydantic import ValidationError

        from app.schemas.executions import ValidateExecutionRequest

        with pytest.raises(ValidationError):
            ValidateExecutionRequest(
                dataset_id=uuid.uuid4(),
                scan_id=uuid.uuid4(),
                model_id=uuid.uuid4(),
                execution_purpose="",
            )

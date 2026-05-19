"""Unit tests for policy thresholds and policy evaluation."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.compliance_policy import CompliancePolicy
from app.models.compliance_rule import ComplianceRule
from app.models.policy_rule import PolicyRule
from app.services.policies.evaluation import PolicyEvaluationEngine
from app.services.policies.thresholds import (
    PolicyThresholdConfig,
    action_from_validation_score,
    resolve_validation_score,
)
from app.services.rules.types import RuleEvaluationContext


def _rule(
    code: str,
    name: str,
    *,
    condition: dict,
    action: str = "block",
    severity: str = "critical",
) -> ComplianceRule:
    return ComplianceRule(
        id=uuid.uuid4(),
        code=code,
        name=name,
        description=name,
        category="data",
        severity=severity,
        action=action,
        priority=50,
        condition_json=condition,
        is_enabled=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _policy(
    name: str,
    *,
    thresholds: dict | None = None,
    rules: list[ComplianceRule] | None = None,
    status: str = "active",
) -> CompliancePolicy:
    policy = CompliancePolicy(
        id=uuid.uuid4(),
        name=name,
        description=None,
        policy_type="execution_policy",
        status=status,
        priority=10,
        definition_json={"thresholds": thresholds or {"block_below": 40, "warn_below": 70}},
        is_active=status == "active",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    policy.policy_rule_links = []
    for idx, rule in enumerate(rules or []):
        policy.policy_rule_links.append(
            PolicyRule(
                policy_id=policy.id,
                rule_id=rule.id,
                sort_order=idx,
                created_at=datetime.now(UTC),
                rule=rule,
            )
        )
    return policy


class TestPolicyThresholds:
    def test_score_below_block(self):
        thresholds = PolicyThresholdConfig(block_below=40, warn_below=70)
        assert action_from_validation_score(30, thresholds) == "block"

    def test_score_in_warn_band(self):
        thresholds = PolicyThresholdConfig(block_below=40, warn_below=70)
        assert action_from_validation_score(50, thresholds) == "warn"

    def test_score_allow(self):
        thresholds = PolicyThresholdConfig(block_below=40, warn_below=70)
        assert action_from_validation_score(80, thresholds) == "allow"

    def test_resolve_from_risk_score(self):
        assert resolve_validation_score(validation_score=None, risk_score=20) == 80
        assert resolve_validation_score(validation_score=55, risk_score=20) == 55


class TestPolicyEvaluation:
    def test_policy_triggers_rule_block(self):
        rule = _rule(
            "data.password",
            "Password detected",
            condition={
                "field": "detected_types",
                "operator": "contains",
                "value": "password",
            },
            action="block",
        )
        policy = _policy("Password policy", rules=[rule])
        engine = PolicyEvaluationEngine()
        ctx = RuleEvaluationContext(detected_types={"password"}, risk_score=10)
        result = engine.evaluate_policy(policy, ctx, validation_score=80)

        assert result.recommended_action == "block"
        assert len(result.triggered_rules) == 1
        assert result.triggered_rules[0].rule_name == "Password detected"

    def test_threshold_block_overrides_high_validation_when_rules_empty(self):
        policy = _policy("Threshold only", rules=[], thresholds={"block_below": 40, "warn_below": 70})
        engine = PolicyEvaluationEngine()
        ctx = RuleEvaluationContext(detected_types=set(), risk_score=90)
        result = engine.evaluate_policy(policy, ctx, validation_score=30)

        assert result.threshold_action == "block"
        assert result.recommended_action == "block"

    def test_threshold_warn_band(self):
        policy = _policy("Warn band", rules=[])
        engine = PolicyEvaluationEngine()
        ctx = RuleEvaluationContext()
        result = engine.evaluate_policy(policy, ctx, validation_score=50)

        assert result.recommended_action == "warn"

    def test_sensitive_external_model_policy(self):
        sensitive_rule = _rule(
            "model.sensitive_external",
            "Sensitive data with external model",
            condition={
                "all": [
                    {
                        "field": "detected_types",
                        "operator": "contains",
                        "value": "api_key",
                    },
                    {"field": "model.is_external", "operator": "equals", "value": True},
                ]
            },
        )
        policy = _policy(
            "External Model Sensitive Data Policy",
            rules=[sensitive_rule],
            thresholds={"block_below": 40, "warn_below": 70},
        )
        engine = PolicyEvaluationEngine()
        ctx = RuleEvaluationContext(
            detected_types={"api_key"},
            model_is_external=True,
            risk_score=10,
        )
        result = engine.evaluate_policy(policy, ctx, validation_score=80)

        assert result.recommended_action == "block"
        assert any(t.rule_name == "Sensitive data with external model" for t in result.triggered_rules)

    def test_evaluate_multiple_active_policies(self):
        rule = _rule(
            "data.email",
            "Email detected",
            condition={
                "field": "detected_types",
                "operator": "contains",
                "value": "email",
            },
            action="warn",
            severity="medium",
        )
        p1 = _policy("P1", rules=[rule])
        p2 = _policy("P2", rules=[], status="inactive")
        engine = PolicyEvaluationEngine()
        ctx = RuleEvaluationContext(detected_types={"email"})
        combined = engine.evaluate_policies([p1, p2], ctx)

        assert combined.policies_evaluated == 1
        assert combined.recommended_action == "warn"

    def test_inactive_policy_excluded_from_bulk_eval(self):
        rule = _rule(
            "data.password",
            "Password",
            condition={
                "field": "detected_types",
                "operator": "contains",
                "value": "password",
            },
        )
        inactive = _policy("Inactive", rules=[rule], status="draft")
        engine = PolicyEvaluationEngine()
        ctx = RuleEvaluationContext(detected_types={"password"})
        combined = engine.evaluate_policies([inactive], ctx)

        assert combined.policies_evaluated == 0
        assert combined.recommended_action == "allow"

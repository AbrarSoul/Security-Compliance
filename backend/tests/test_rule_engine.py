"""Unit tests for the database-driven compliance rule engine."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.compliance_rule import ComplianceRule
from app.services.rules import (
    RuleEngine,
    RuleEvaluationContext,
    aggregate_triggered_rules,
    context_from_detections,
    evaluate_condition,
)
from app.services.rules.types import TriggeredRule
from app.services.scanner.types import DetectionResult


def _rule(
    code: str,
    name: str,
    *,
    condition: dict,
    severity: str = "medium",
    action: str = "warn",
    priority: int = 0,
    category: str = "data",
    enabled: bool = True,
) -> ComplianceRule:
    return ComplianceRule(
        id=uuid.uuid4(),
        code=code,
        name=name,
        description=f"Test rule {name}",
        category=category,
        severity=severity,
        action=action,
        priority=priority,
        condition_json=condition,
        is_enabled=enabled,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestConditionEvaluator:
    def test_contains_detected_type(self):
        ctx = RuleEvaluationContext(detected_types={"email", "phone"})
        cond = {"field": "detected_types", "operator": "contains", "value": "email"}
        assert evaluate_condition(cond, ctx) is True

    def test_contains_missing_type(self):
        ctx = RuleEvaluationContext(detected_types={"phone"})
        cond = {"field": "detected_types", "operator": "contains", "value": "email"}
        assert evaluate_condition(cond, ctx) is False

    def test_all_compound(self):
        ctx = RuleEvaluationContext(
            detected_types={"password"},
            model_is_external=True,
        )
        cond = {
            "all": [
                {"field": "detected_types", "operator": "contains", "value": "password"},
                {"field": "model.is_external", "operator": "equals", "value": True},
            ]
        }
        assert evaluate_condition(cond, ctx) is True

    def test_classification_in(self):
        ctx = RuleEvaluationContext(classification="confidential")
        cond = {
            "field": "classification",
            "operator": "in",
            "value": ["confidential", "restricted"],
        }
        assert evaluate_condition(cond, ctx) is True

    def test_any_compound(self):
        ctx = RuleEvaluationContext(detected_types={"api_key"})
        cond = {
            "any": [
                {"field": "detected_types", "operator": "contains", "value": "email"},
                {"field": "detected_types", "operator": "contains", "value": "api_key"},
            ]
        }
        assert evaluate_condition(cond, ctx) is True


class TestRuleEngine:
    def test_email_warn_rule(self):
        engine = RuleEngine()
        rules = [
            _rule(
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
        ]
        ctx = RuleEvaluationContext(detected_types={"email"})
        result = engine.evaluate(rules, ctx)
        assert len(result.triggered_rules) == 1
        assert result.triggered_rules[0].action == "warn"
        assert result.recommended_action == "warn"
        assert result.aggregated_severity == "medium"

    def test_password_block_rule(self):
        engine = RuleEngine()
        rules = [
            _rule(
                "data.password",
                "Password detected",
                condition={
                    "field": "detected_types",
                    "operator": "contains",
                    "value": "password",
                },
                action="block",
                severity="critical",
                priority=90,
            )
        ]
        ctx = RuleEvaluationContext(detected_types={"password"})
        result = engine.evaluate(rules, ctx)
        assert result.recommended_action == "block"
        assert result.aggregated_severity == "critical"
        assert "Password" in result.decision_reason

    def test_disabled_rules_skipped(self):
        engine = RuleEngine()
        rules = [
            _rule(
                "data.password",
                "Password",
                condition={
                    "field": "detected_types",
                    "operator": "contains",
                    "value": "password",
                },
                action="block",
                enabled=False,
            )
        ]
        ctx = RuleEvaluationContext(detected_types={"password"})
        result = engine.evaluate(rules, ctx)
        assert result.triggered_rules == []
        assert result.recommended_action == "allow"

    def test_priority_higher_evaluated_first_but_all_trigger(self):
        engine = RuleEngine()
        rules = [
            _rule(
                "data.email",
                "Email",
                condition={
                    "field": "detected_types",
                    "operator": "contains",
                    "value": "email",
                },
                action="warn",
                priority=10,
            ),
            _rule(
                "data.password",
                "Password",
                condition={
                    "field": "detected_types",
                    "operator": "contains",
                    "value": "password",
                },
                action="block",
                priority=100,
            ),
        ]
        ctx = RuleEvaluationContext(detected_types={"email", "password"})
        result = engine.evaluate(rules, ctx)
        assert len(result.triggered_rules) == 2
        assert result.recommended_action == "block"

    def test_sensitive_external_model_compound(self):
        engine = RuleEngine()
        rules = [
            _rule(
                "model.sensitive_external",
                "Sensitive + external",
                category="model",
                condition={
                    "all": [
                        {
                            "any": [
                                {
                                    "field": "detected_types",
                                    "operator": "contains",
                                    "value": "api_key",
                                },
                                {
                                    "field": "detected_types",
                                    "operator": "contains",
                                    "value": "sensitive_field",
                                },
                            ]
                        },
                        {
                            "field": "model.is_external",
                            "operator": "equals",
                            "value": True,
                        },
                    ]
                },
                action="block",
                severity="critical",
            )
        ]
        ctx = RuleEvaluationContext(
            detected_types={"sensitive_field"},
            model_is_external=True,
        )
        result = engine.evaluate(rules, ctx)
        assert len(result.triggered_rules) == 1
        assert result.recommended_action == "block"

    def test_context_from_detections(self):
        detections = [
            DetectionResult(
                finding_type="email",
                severity="medium",
                column_name="email_col",
                sample_count=5,
                match_rate=0.5,
                evidence={},
            )
        ]
        ctx = context_from_detections(detections, classification="confidential")
        assert "email" in ctx.detected_types
        assert ctx.classification == "confidential"


class TestRiskAggregation:
    def test_no_rules_triggered(self):
        result = aggregate_triggered_rules([], rules_evaluated=3)
        assert result.aggregated_risk_score == 0
        assert result.recommended_action == "allow"

    def test_multiple_severities_aggregate(self):
        triggered = [
            TriggeredRule(
                rule_id=uuid.uuid4(),
                rule_name="A",
                rule_code="a",
                category="data",
                severity="medium",
                action="warn",
                priority=1,
                reason="warn",
            ),
            TriggeredRule(
                rule_id=uuid.uuid4(),
                rule_name="B",
                rule_code="b",
                category="security",
                severity="critical",
                action="block",
                priority=2,
                reason="block",
            ),
        ]
        result = aggregate_triggered_rules(triggered, rules_evaluated=5)
        assert result.aggregated_risk_score == 65  # 15 + 50 capped at 100
        assert result.aggregated_severity == "critical"
        assert result.recommended_action == "block"

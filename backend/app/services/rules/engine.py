"""Evaluate enabled compliance rules from the database against a context."""

import logging
from typing import Any

from app.models.compliance_rule import ComplianceRule
from app.services.rules.aggregation import aggregate_triggered_rules
from app.services.rules.conditions import ConditionEvaluationError, evaluate_condition
from app.services.rules.types import (
    RuleEvaluationContext,
    RuleEvaluationResult,
    TriggeredRule,
)

logger = logging.getLogger(__name__)


class RuleEngine:
    """Database-driven rule evaluation (no hardcoded rules in scanner)."""

    def evaluate(
        self,
        rules: list[ComplianceRule],
        ctx: RuleEvaluationContext,
    ) -> RuleEvaluationResult:
        enabled = [r for r in rules if r.is_enabled]
        enabled.sort(key=lambda r: (-(r.priority or 0), r.name))

        triggered: list[TriggeredRule] = []
        for rule in enabled:
            condition = rule.condition_json or {}
            try:
                if not evaluate_condition(condition, ctx):
                    continue
            except ConditionEvaluationError as exc:
                logger.warning("Rule %s condition error: %s", rule.code, exc)
                continue
            except Exception as exc:
                logger.exception("Rule %s evaluation failed: %s", rule.code, exc)
                continue

            triggered.append(
                TriggeredRule(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    rule_code=rule.code,
                    category=rule.category,
                    severity=rule.severity,
                    action=rule.action,
                    priority=rule.priority or 0,
                    reason=_build_reason(rule, ctx),
                )
            )

        return aggregate_triggered_rules(triggered, rules_evaluated=len(enabled))


def _build_reason(rule: ComplianceRule, ctx: RuleEvaluationContext) -> str:
    if rule.description:
        return rule.description
    condition = rule.condition_json or {}
    field = condition.get("field")
    value = condition.get("value")
    if field == "detected_types" and value:
        return f"Dataset contains {value}"
    if field == "classification" and value:
        return f"Classification is {value}"
    return f"Rule {rule.name} matched"


def build_triggered_rule_dict(triggered: TriggeredRule) -> dict[str, Any]:
    """Public shape for API responses (rule_id as int-like string UUID)."""
    return {
        "rule_id": str(triggered.rule_id),
        "rule_name": triggered.rule_name,
        "severity": triggered.severity,
        "action": triggered.action,
        "reason": triggered.reason,
    }

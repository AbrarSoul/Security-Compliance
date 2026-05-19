"""Aggregate triggered rules into risk score and recommended action."""

from app.services.rules.constants import (
    ACTION_ORDER,
    SEVERITY_ORDER,
    SEVERITY_RISK_POINTS,
)
from app.services.rules.types import RuleEvaluationResult, TriggeredRule


def aggregate_triggered_rules(
    triggered: list[TriggeredRule],
    *,
    rules_evaluated: int,
) -> RuleEvaluationResult:
    if not triggered:
        return RuleEvaluationResult(
            triggered_rules=[],
            rules_evaluated=rules_evaluated,
            aggregated_risk_score=0,
            aggregated_severity=None,
            recommended_action="allow",
            decision_reason="No rules triggered",
        )

    risk_score = min(
        100,
        sum(SEVERITY_RISK_POINTS.get(t.severity, 10) for t in triggered),
    )

    worst_severity = max(triggered, key=lambda t: SEVERITY_ORDER.get(t.severity, 0)).severity
    worst_action = max(triggered, key=lambda t: ACTION_ORDER.get(t.action, 0)).action

    block_rules = [t for t in triggered if t.action == "block"]
    if block_rules:
        top = max(block_rules, key=lambda t: (SEVERITY_ORDER.get(t.severity, 0), t.priority))
        decision_reason = f"Blocked by rule: {top.rule_name}"
    else:
        warn_rules = [t for t in triggered if t.action == "warn"]
        if warn_rules:
            top = max(warn_rules, key=lambda t: (SEVERITY_ORDER.get(t.severity, 0), t.priority))
            decision_reason = f"Warning from rule: {top.rule_name}"
        else:
            decision_reason = f"{len(triggered)} rule(s) triggered with allow action"

    return RuleEvaluationResult(
        triggered_rules=triggered,
        rules_evaluated=rules_evaluated,
        aggregated_risk_score=risk_score,
        aggregated_severity=worst_severity,
        recommended_action=worst_action,
        decision_reason=decision_reason,
    )

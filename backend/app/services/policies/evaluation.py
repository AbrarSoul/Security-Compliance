"""Evaluate active policies using the rule engine and threshold bands."""

from app.models.compliance_policy import CompliancePolicy
from app.models.compliance_rule import ComplianceRule
from app.services.policies.thresholds import (
    PolicyThresholdConfig,
    action_from_validation_score,
    resolve_validation_score,
    threshold_decision_reason,
)
from app.services.policies.types import PoliciesEvaluationResult, PolicyEvaluationResult
from app.services.rules.constants import ACTION_ORDER
from app.services.rules.engine import RuleEngine
from app.services.rules.types import RuleEvaluationContext


class PolicyEvaluationEngine:
    def __init__(self, rule_engine: RuleEngine | None = None):
        self.rule_engine = rule_engine or RuleEngine()

    def evaluate_policies(
        self,
        policies: list[CompliancePolicy],
        ctx: RuleEvaluationContext,
        *,
        validation_score: int | None = None,
    ) -> PoliciesEvaluationResult:
        score = resolve_validation_score(
            validation_score=validation_score,
            risk_score=ctx.risk_score,
        )

        active_policies = [p for p in policies if p.status == "active"]
        active_policies.sort(key=lambda p: (-(p.priority or 0), p.name))

        results: list[PolicyEvaluationResult] = []
        for policy in active_policies:
            results.append(self.evaluate_policy(policy, ctx, validation_score=score))

        if not results:
            return PoliciesEvaluationResult(
                policy_results=[],
                policies_evaluated=0,
                recommended_action="allow",
                decision_reason="No active policies evaluated",
            )

        worst = max(results, key=lambda r: ACTION_ORDER.get(r.recommended_action, 0))
        return PoliciesEvaluationResult(
            policy_results=results,
            policies_evaluated=len(results),
            recommended_action=worst.recommended_action,
            decision_reason=worst.decision_reason,
        )

    def evaluate_policy(
        self,
        policy: CompliancePolicy,
        ctx: RuleEvaluationContext,
        *,
        validation_score: int | None = None,
    ) -> PolicyEvaluationResult:
        score = resolve_validation_score(
            validation_score=validation_score,
            risk_score=ctx.risk_score,
        )
        thresholds = PolicyThresholdConfig.from_dict(
            (policy.definition_json or {}).get("thresholds")
        )

        rules = self._policy_rules(policy)
        rule_result = self.rule_engine.evaluate(rules, ctx)

        threshold_action: str | None = None
        if score is not None:
            threshold_action = action_from_validation_score(score, thresholds)

        recommended_action, decision_reason = self._combine_decisions(
            policy_name=policy.name,
            rule_result=rule_result,
            threshold_action=threshold_action,
            validation_score=score,
            thresholds=thresholds,
        )

        return PolicyEvaluationResult(
            policy_id=policy.id,
            policy_name=policy.name,
            policy_type=policy.policy_type,
            status=policy.status,
            priority=policy.priority or 0,
            validation_score=score,
            threshold_action=threshold_action,
            rule_evaluation=rule_result,
            recommended_action=recommended_action,
            decision_reason=decision_reason,
            triggered_rules=rule_result.triggered_rules,
        )

    def _policy_rules(self, policy: CompliancePolicy) -> list[ComplianceRule]:
        links = sorted(
            policy.policy_rule_links or [],
            key=lambda link: (link.sort_order, link.rule.name if link.rule else ""),
        )
        return [link.rule for link in links if link.rule is not None]

    def _combine_decisions(
        self,
        *,
        policy_name: str,
        rule_result,
        threshold_action: str | None,
        validation_score: int | None,
        thresholds: PolicyThresholdConfig,
    ) -> tuple[str, str]:
        actions: list[tuple[str, str]] = []

        if rule_result.triggered_rules:
            actions.append(
                (rule_result.recommended_action, rule_result.decision_reason)
            )

        if threshold_action is not None and validation_score is not None:
            actions.append(
                (
                    threshold_action,
                    threshold_decision_reason(
                        validation_score, threshold_action, thresholds
                    ),
                )
            )

        if not actions:
            return "allow", f"Policy '{policy_name}': no rules triggered and no score thresholds applied"

        worst_action = max(actions, key=lambda item: ACTION_ORDER.get(item[0], 0))
        return worst_action[0], f"Policy '{policy_name}': {worst_action[1]}"

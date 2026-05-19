"""Aggregate rule, policy, model, and scan signals into a pre-execution decision."""

from dataclasses import dataclass, field
from typing import Any

from app.services.execution.constants import DECISION_ORDER, RISK_LEVEL_ORDER
from app.services.model_compliance.types import ModelComplianceCheckResult
from app.services.policies.types import PoliciesEvaluationResult
from app.services.rules.types import RuleEvaluationResult


@dataclass
class PolicyViolation:
    policy_id: str
    policy_name: str
    policy_type: str
    action: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "policy_type": self.policy_type,
            "action": self.action,
            "reason": self.reason,
        }


@dataclass
class PreExecutionValidationOutcome:
    decision: str
    risk_score: int
    risk_level: str
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    policy_violations: list[PolicyViolation] = field(default_factory=list)
    model_risks: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    explanation: str = ""
    reason_codes: list[str] = field(default_factory=list)
    rule_evaluation: dict[str, Any] | None = None
    policy_evaluation: dict[str, Any] | None = None
    model_evaluation: dict[str, Any] | None = None

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "triggered_rules": self.triggered_rules,
            "policy_violations": [v.to_dict() for v in self.policy_violations],
            "model_risks": self.model_risks,
            "recommendations": self.recommendations,
            "explanation": self.explanation,
            "reason_codes": self.reason_codes,
            "rule_evaluation": self.rule_evaluation,
            "policy_evaluation": self.policy_evaluation,
            "model_evaluation": self.model_evaluation,
        }


class PreExecutionValidator:
    """Combine scan, rules, policies, and model compliance into a final decision."""

    def aggregate(
        self,
        *,
        scan_risk_score: int | None,
        scan_classification: str | None,
        rule_result: RuleEvaluationResult,
        policy_result: PoliciesEvaluationResult,
        model_result: ModelComplianceCheckResult,
        recommendations: list[str] | None = None,
    ) -> PreExecutionValidationOutcome:
        triggered_rules = [t.to_dict() for t in rule_result.triggered_rules]
        policy_violations = self._policy_violations(policy_result)
        model_risks = [c.to_dict() for c in model_result.risk_checks if c.triggered]

        decisions: list[tuple[str, str, str]] = [
            (
                rule_result.recommended_action,
                rule_result.aggregated_severity or "low",
                rule_result.decision_reason,
            ),
            (
                policy_result.recommended_action,
                self._policy_risk_level(policy_result),
                policy_result.decision_reason,
            ),
            (
                model_result.decision,
                model_result.risk_level,
                model_result.primary_reason,
            ),
        ]

        worst = max(decisions, key=lambda d: DECISION_ORDER.get(d[0], 0))
        decision, risk_level, explanation = worst[0], worst[1], worst[2]

        risk_score = self._compute_risk_score(
            scan_risk_score=scan_risk_score,
            rule_result=rule_result,
            model_result=model_result,
        )

        merged_recs = list(
            dict.fromkeys((recommendations or []) + model_result.recommendations)
        )
        reason_codes = self._reason_codes(
            rule_result, policy_violations, model_risks, scan_classification
        )

        if decision == "block" and "block" not in explanation.lower():
            explanation = f"Execution blocked: {explanation}"
        elif decision == "warn":
            explanation = f"Execution may proceed with caution: {explanation}"

        return PreExecutionValidationOutcome(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            triggered_rules=triggered_rules,
            policy_violations=policy_violations,
            model_risks=model_risks,
            recommendations=merged_recs,
            explanation=explanation,
            reason_codes=reason_codes,
            rule_evaluation=rule_result.to_dict(),
            policy_evaluation=policy_result.to_dict(),
            model_evaluation=model_result.to_dict(),
        )

    def _policy_violations(
        self, policy_result: PoliciesEvaluationResult
    ) -> list[PolicyViolation]:
        violations: list[PolicyViolation] = []
        for result in policy_result.policy_results:
            action = result.recommended_action
            if action in ("warn", "block"):
                violations.append(
                    PolicyViolation(
                        policy_id=str(result.policy_id),
                        policy_name=result.policy_name,
                        policy_type=result.policy_type,
                        action=action,
                        reason=result.decision_reason,
                    )
                )
        return violations

    @staticmethod
    def _policy_risk_level(policy_result: PoliciesEvaluationResult) -> str:
        levels: list[str] = []
        for result in policy_result.policy_results:
            sev = result.rule_evaluation.aggregated_severity
            if sev:
                levels.append(sev)
            if result.threshold_action == "block":
                levels.append("critical")
            elif result.threshold_action == "warn":
                levels.append("high")
        if not levels:
            return "low"
        return max(levels, key=lambda s: RISK_LEVEL_ORDER.get(s, 0))

    @staticmethod
    def _compute_risk_score(
        *,
        scan_risk_score: int | None,
        rule_result: RuleEvaluationResult,
        model_result: ModelComplianceCheckResult,
    ) -> int:
        parts = [
            scan_risk_score or 0,
            rule_result.aggregated_risk_score,
            model_result.risk_score,
        ]
        return min(100, max(parts))

    @staticmethod
    def _reason_codes(
        rule_result: RuleEvaluationResult,
        policy_violations: list[PolicyViolation],
        model_risks: list[dict[str, Any]],
        classification: str | None,
    ) -> list[str]:
        codes: list[str] = []
        for rule in rule_result.triggered_rules:
            codes.append(f"rule:{rule.rule_code}")
        for violation in policy_violations:
            codes.append(f"policy:{violation.policy_type}:{violation.action}")
        for risk in model_risks:
            codes.append(f"model:{risk['code']}")
        if classification in ("confidential", "restricted"):
            codes.append(f"classification:{classification}")
        return list(dict.fromkeys(codes))

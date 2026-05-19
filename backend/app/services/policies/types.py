from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.services.rules.types import RuleEvaluationResult, TriggeredRule


@dataclass
class PolicyEvaluationResult:
    policy_id: UUID
    policy_name: str
    policy_type: str
    status: str
    priority: int
    validation_score: int | None
    threshold_action: str | None
    rule_evaluation: RuleEvaluationResult
    recommended_action: str
    decision_reason: str
    triggered_rules: list[TriggeredRule] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_id": str(self.policy_id),
            "policy_name": self.policy_name,
            "policy_type": self.policy_type,
            "status": self.status,
            "priority": self.priority,
            "validation_score": self.validation_score,
            "threshold_action": self.threshold_action,
            "rule_evaluation": self.rule_evaluation.to_dict(),
            "recommended_action": self.recommended_action,
            "decision_reason": self.decision_reason,
            "triggered_rules": [t.to_dict() for t in self.triggered_rules],
        }


@dataclass
class PoliciesEvaluationResult:
    policy_results: list[PolicyEvaluationResult] = field(default_factory=list)
    policies_evaluated: int = 0
    recommended_action: str = "allow"
    decision_reason: str = "No active policies evaluated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_results": [p.to_dict() for p in self.policy_results],
            "policies_evaluated": self.policies_evaluated,
            "recommended_action": self.recommended_action,
            "decision_reason": self.decision_reason,
        }

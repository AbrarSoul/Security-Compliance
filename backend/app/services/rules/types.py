from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class RuleEvaluationContext:
    """Facts available when evaluating compliance rules (not hardcoded in scanner)."""

    detected_types: set[str] = field(default_factory=set)
    risk_score: int | None = None
    compliance_status: str | None = None
    classification: str | None = None
    model_is_external: bool = False
    model_deployment: str | None = None
    model_provider: str | None = None
    findings_count: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def get_field(self, path: str) -> Any:
        """Resolve dotted field paths against the evaluation context."""
        if path in ("detected_types", "finding_types"):
            return self.detected_types
        if path == "risk_score":
            return self.risk_score
        if path == "compliance_status":
            return self.compliance_status
        if path == "classification":
            return self.classification
        if path in ("model.is_external", "model_is_external"):
            return self.model_is_external
        if path in ("model.deployment", "model_deployment"):
            return self.model_deployment
        if path in ("model.provider", "model_provider"):
            return self.model_provider
        if path == "findings_count":
            return self.findings_count
        if path in self.extra:
            return self.extra[path]
        return None


@dataclass
class TriggeredRule:
    rule_id: UUID
    rule_name: str
    rule_code: str
    category: str
    severity: str
    action: str
    priority: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": str(self.rule_id),
            "rule_name": self.rule_name,
            "rule_code": self.rule_code,
            "category": self.category,
            "severity": self.severity,
            "action": self.action,
            "priority": self.priority,
            "reason": self.reason,
        }


@dataclass
class RuleEvaluationResult:
    triggered_rules: list[TriggeredRule] = field(default_factory=list)
    rules_evaluated: int = 0
    aggregated_risk_score: int = 0
    aggregated_severity: str | None = None
    recommended_action: str = "allow"
    decision_reason: str = "No rules triggered"

    def to_dict(self) -> dict[str, Any]:
        return {
            "triggered_rules": [t.to_dict() for t in self.triggered_rules],
            "rules_evaluated": self.rules_evaluated,
            "aggregated_risk_score": self.aggregated_risk_score,
            "aggregated_severity": self.aggregated_severity,
            "recommended_action": self.recommended_action,
            "decision_reason": self.decision_reason,
        }

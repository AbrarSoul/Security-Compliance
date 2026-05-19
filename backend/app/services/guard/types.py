from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass
class GuardDecision:
    decision: str
    risk_score: int
    risk_level: str
    source: str
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "source": self.source,
            "reasons": self.reasons,
        }


@dataclass
class GuardResult:
    allowed: bool
    decision: str
    risk_score: int
    risk_level: str
    execution_request_id: UUID
    session_id: UUID | None = None
    prompt_scan_id: UUID | None = None
    output_scan_id: UUID | None = None
    interrupted: bool = False
    execution_status: str | None = None
    blocking_reasons: list[str] = field(default_factory=list)
    warning_reasons: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    masked_content: str | None = None
    redacted_content: str | None = None
    scan_decision: GuardDecision | None = None
    rule_decision: GuardDecision | None = None
    policy_decision: GuardDecision | None = None
    triggered_rules: list[dict[str, Any]] = field(default_factory=list)
    policy_violations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "decision": self.decision,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "execution_request_id": str(self.execution_request_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "prompt_scan_id": str(self.prompt_scan_id) if self.prompt_scan_id else None,
            "output_scan_id": str(self.output_scan_id) if self.output_scan_id else None,
            "interrupted": self.interrupted,
            "execution_status": self.execution_status,
            "blocking_reasons": self.blocking_reasons,
            "warning_reasons": self.warning_reasons,
            "recommendations": self.recommendations,
            "masked_content": self.masked_content,
            "redacted_content": self.redacted_content,
            "scan_decision": self.scan_decision.to_dict() if self.scan_decision else None,
            "rule_decision": self.rule_decision.to_dict() if self.rule_decision else None,
            "policy_decision": self.policy_decision.to_dict() if self.policy_decision else None,
            "triggered_rules": self.triggered_rules,
            "policy_violations": self.policy_violations,
        }

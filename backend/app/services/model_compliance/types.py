from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelRiskCheck:
    code: str
    title: str
    description: str
    risk_level: str
    suggested_action: str
    triggered: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "risk_level": self.risk_level,
            "suggested_action": self.suggested_action,
            "triggered": self.triggered,
        }


@dataclass
class DatasetContext:
    detected_types: set[str] = field(default_factory=set)
    classification: str | None = None
    risk_score: int | None = None
    compliance_status: str | None = None

    @property
    def has_sensitive_data(self) -> bool:
        from app.services.model_compliance.constants import SENSITIVE_FINDING_TYPES

        return bool(self.detected_types & SENSITIVE_FINDING_TYPES)

    @property
    def has_pii(self) -> bool:
        return bool(self.detected_types & {"email", "phone", "name"})

    @property
    def is_high_risk_classification(self) -> bool:
        from app.services.model_compliance.constants import HIGH_RISK_CLASSIFICATIONS

        if not self.classification:
            return False
        return self.classification.lower() in HIGH_RISK_CLASSIFICATIONS


@dataclass
class ModelContext:
    name: str
    provider: str | None
    model_type: str
    endpoint_url: str | None = None
    data_retention_policy: str | None = None
    logging_enabled: bool | None = None
    data_leaves_platform: bool = False
    is_approved: bool = False

    @property
    def is_external(self) -> bool:
        return self.model_type in ("external_api", "cloud_hosted") or self.data_leaves_platform

    @property
    def is_cloud(self) -> bool:
        return self.model_type == "cloud_hosted"

    @property
    def provider_unknown(self) -> bool:
        from app.services.model_compliance.constants import UNKNOWN_PROVIDERS

        if not self.provider:
            return True
        return self.provider.strip().lower() in UNKNOWN_PROVIDERS

    @property
    def stores_user_data(self) -> bool:
        if not self.data_retention_policy:
            return False
        policy = self.data_retention_policy.lower()
        return any(
            token in policy
            for token in ("store", "retain", "persist", "keep", "save")
        )

    @property
    def lacks_privacy_metadata(self) -> bool:
        return (
            self.data_retention_policy is None
            and self.logging_enabled is None
            and self.data_leaves_platform
        )


@dataclass
class ModelComplianceCheckResult:
    risk_checks: list[ModelRiskCheck] = field(default_factory=list)
    risk_level: str = "low"
    risk_score: int = 0
    decision: str = "allow"
    primary_reason: str = "No significant model compliance risks detected"
    recommendations: list[str] = field(default_factory=list)
    rule_evaluation: dict[str, Any] | None = None
    policy_evaluation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_checks": [c.to_dict() for c in self.risk_checks],
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "decision": self.decision,
            "primary_reason": self.primary_reason,
            "recommendations": self.recommendations,
            "rule_evaluation": self.rule_evaluation,
            "policy_evaluation": self.policy_evaluation,
        }

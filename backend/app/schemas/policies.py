from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.rules import ComplianceRuleResponse, RuleEvaluationResponse, TriggeredRuleResponse
from app.services.policies.constants import POLICY_STATUSES, POLICY_TYPES


class PolicyThresholdsSchema(BaseModel):
    block_below: int = Field(default=40, ge=0, le=100)
    warn_below: int = Field(default=70, ge=0, le=100)

    @field_validator("warn_below")
    @classmethod
    def warn_above_block(cls, warn_below: int, info) -> int:
        block_below = info.data.get("block_below", 40)
        if warn_below <= block_below:
            raise ValueError("warn_below must be greater than block_below")
        return warn_below


class CompliancePolicyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    policy_type: str
    priority: int = Field(default=0, ge=0, le=1000)
    thresholds: PolicyThresholdsSchema = Field(default_factory=PolicyThresholdsSchema)

    @field_validator("policy_type")
    @classmethod
    def validate_policy_type(cls, value: str) -> str:
        if value not in POLICY_TYPES:
            raise ValueError(f"policy_type must be one of: {', '.join(sorted(POLICY_TYPES))}")
        return value


class CompliancePolicyCreate(CompliancePolicyBase):
    status: str = "draft"
    rule_ids: list[UUID] = Field(default_factory=list)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in POLICY_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(POLICY_STATUSES))}")
        return value


class CompliancePolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    policy_type: str | None = None
    priority: int | None = Field(default=None, ge=0, le=1000)
    thresholds: PolicyThresholdsSchema | None = None

    @field_validator("policy_type")
    @classmethod
    def validate_policy_type(cls, value: str | None) -> str | None:
        if value is not None and value not in POLICY_TYPES:
            raise ValueError(f"policy_type must be one of: {', '.join(sorted(POLICY_TYPES))}")
        return value


class PolicyRuleLinkResponse(BaseModel):
    rule_id: UUID
    sort_order: int
    rule: ComplianceRuleResponse | None = None


class CompliancePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    policy_type: str
    status: str
    priority: int
    thresholds: PolicyThresholdsSchema
    is_active: bool
    severity_default: str | None
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime
    rules: list[ComplianceRuleResponse] = Field(default_factory=list)


class CompliancePolicyListResponse(BaseModel):
    items: list[CompliancePolicyResponse]
    total: int
    limit: int
    offset: int


class AttachPolicyRulesRequest(BaseModel):
    rule_ids: list[UUID] = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)


class DetachPolicyRulesRequest(BaseModel):
    rule_ids: list[UUID] = Field(min_length=1)


class EvaluatePoliciesRequest(BaseModel):
    detected_types: list[str] = Field(default_factory=list)
    risk_score: int | None = Field(default=None, ge=0, le=100)
    validation_score: int | None = Field(default=None, ge=0, le=100)
    compliance_status: str | None = None
    classification: str | None = None
    model_is_external: bool = False
    model_deployment: str | None = None
    model_provider: str | None = None
    policy_id: UUID | None = Field(
        default=None,
        description="Evaluate a single policy; omit to evaluate all active policies",
    )


class PolicyEvaluationResponse(BaseModel):
    policy_id: UUID
    policy_name: str
    policy_type: str
    status: str
    priority: int
    validation_score: int | None
    threshold_action: str | None
    rule_evaluation: RuleEvaluationResponse
    recommended_action: str
    decision_reason: str
    triggered_rules: list[TriggeredRuleResponse]


class PoliciesEvaluationResponse(BaseModel):
    policy_results: list[PolicyEvaluationResponse]
    policies_evaluated: int
    recommended_action: str
    decision_reason: str

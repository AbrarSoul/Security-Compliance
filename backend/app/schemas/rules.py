from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.rules.constants import (
    RULE_ACTIONS,
    RULE_CATEGORIES,
    RULE_SEVERITIES,
)


class RuleConditionSchema(BaseModel):
    """Structured JSON condition (leaf or compound)."""

    field: str | None = None
    operator: str | None = None
    value: Any = None
    all: list["RuleConditionSchema"] | None = None
    any: list["RuleConditionSchema"] | None = None
    not_: dict[str, Any] | None = Field(default=None, alias="not")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class ComplianceRuleBase(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str
    severity: str
    action: str
    priority: int = Field(default=0, ge=0, le=1000)
    condition: dict[str, Any] = Field(
        description="JSON condition (field/operator/value or all/any/not)",
    )
    is_enabled: bool = True

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        if value not in RULE_CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(RULE_CATEGORIES))}")
        return value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        if value not in RULE_SEVERITIES:
            raise ValueError(f"severity must be one of: {', '.join(sorted(RULE_SEVERITIES))}")
        return value

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str) -> str:
        if value not in RULE_ACTIONS:
            raise ValueError(f"action must be one of: {', '.join(sorted(RULE_ACTIONS))}")
        return value


class ComplianceRuleCreate(ComplianceRuleBase):
    pass


class ComplianceRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = None
    severity: str | None = None
    action: str | None = None
    priority: int | None = Field(default=None, ge=0, le=1000)
    condition: dict[str, Any] | None = None
    is_enabled: bool | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is not None and value not in RULE_CATEGORIES:
            raise ValueError(f"category must be one of: {', '.join(sorted(RULE_CATEGORIES))}")
        return value

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str | None) -> str | None:
        if value is not None and value not in RULE_SEVERITIES:
            raise ValueError(f"severity must be one of: {', '.join(sorted(RULE_SEVERITIES))}")
        return value

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: str | None) -> str | None:
        if value is not None and value not in RULE_ACTIONS:
            raise ValueError(f"action must be one of: {', '.join(sorted(RULE_ACTIONS))}")
        return value


class ComplianceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    category: str
    severity: str
    action: str
    priority: int
    condition: dict[str, Any] | None = Field(validation_alias="condition_json")
    is_enabled: bool
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ComplianceRuleListResponse(BaseModel):
    items: list[ComplianceRuleResponse]
    total: int
    limit: int
    offset: int


class TriggeredRuleResponse(BaseModel):
    rule_id: UUID
    rule_name: str
    severity: str
    action: str
    reason: str
    rule_code: str | None = None
    category: str | None = None
    priority: int | None = None


class RuleEvaluationResponse(BaseModel):
    triggered_rules: list[TriggeredRuleResponse]
    rules_evaluated: int
    aggregated_risk_score: int
    aggregated_severity: str | None
    recommended_action: str
    decision_reason: str


class EvaluateRulesRequest(BaseModel):
    detected_types: list[str] = Field(default_factory=list)
    risk_score: int | None = None
    compliance_status: str | None = None
    classification: str | None = None
    model_is_external: bool = False
    model_deployment: str | None = None
    model_provider: str | None = None

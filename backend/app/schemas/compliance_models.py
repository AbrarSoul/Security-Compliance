from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.policies import PoliciesEvaluationResponse
from app.schemas.rules import RuleEvaluationResponse
from app.services.model_compliance.constants import DECISIONS, MODEL_TYPES, RISK_LEVELS


class ComplianceModelBase(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=255)
    provider: str | None = None
    model_type: str
    endpoint_url: str | None = None
    data_retention_policy: str | None = None
    logging_enabled: bool | None = None
    data_leaves_platform: bool = False
    is_approved: bool = False
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, value: str) -> str:
        if value not in MODEL_TYPES:
            raise ValueError(f"model_type must be one of: {', '.join(sorted(MODEL_TYPES))}")
        return value


class ComplianceModelCreate(ComplianceModelBase):
    pass


class ComplianceModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = None
    model_type: str | None = None
    endpoint_url: str | None = None
    data_retention_policy: str | None = None
    logging_enabled: bool | None = None
    data_leaves_platform: bool | None = None
    is_approved: bool | None = None
    is_active: bool | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, value: str | None) -> str | None:
        if value is not None and value not in MODEL_TYPES:
            raise ValueError(f"model_type must be one of: {', '.join(sorted(MODEL_TYPES))}")
        return value


class ComplianceModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    provider: str | None
    model_type: str
    endpoint_url: str | None
    data_retention_policy: str | None
    logging_enabled: bool | None
    data_leaves_platform: bool
    is_approved: bool
    is_active: bool
    metadata: dict[str, Any] | None = Field(validation_alias="metadata_json")
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ComplianceModelListResponse(BaseModel):
    items: list[ComplianceModelResponse]
    total: int
    limit: int
    offset: int


class ModelRiskCheckResponse(BaseModel):
    code: str
    title: str
    description: str
    risk_level: str
    suggested_action: str
    triggered: bool


class ValidateModelRequest(BaseModel):
    scan_id: UUID
    model_id: UUID | None = None
    model_code: str | None = None

    @model_validator(mode="after")
    def require_model_ref(self) -> "ValidateModelRequest":
        if not self.model_id and not self.model_code:
            raise ValueError("Either model_id or model_code is required")
        return self


class ModelComplianceValidationResponse(BaseModel):
    id: UUID
    scan_id: UUID
    model_id: UUID
    model_name: str
    model_type: str
    provider: str | None
    decision: str
    risk_level: str
    risk_score: int
    primary_reason: str
    recommendations: list[str]
    risk_checks: list[ModelRiskCheckResponse]
    rule_evaluation: RuleEvaluationResponse | None = None
    policy_evaluation: PoliciesEvaluationResponse | None = None
    dataset_classification: str | None = None
    detected_types: list[str] = Field(default_factory=list)
    validated_at: datetime | None
    created_at: datetime

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        if value not in DECISIONS:
            raise ValueError(f"decision must be one of: {', '.join(sorted(DECISIONS))}")
        return value

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, value: str) -> str:
        if value not in RISK_LEVELS:
            raise ValueError(f"risk_level must be one of: {', '.join(sorted(RISK_LEVELS))}")
        return value

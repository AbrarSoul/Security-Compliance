from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.execution.constants import DECISIONS


class ValidateExecutionRequest(BaseModel):
    dataset_id: UUID = Field(description="Uploaded file (dataset) id")
    scan_id: UUID
    model_id: UUID
    execution_purpose: str = Field(min_length=1, max_length=2000)


class TriggeredRuleSummary(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    action: str
    reason: str
    rule_code: str | None = None


class PolicyViolationSummary(BaseModel):
    policy_id: str
    policy_name: str
    policy_type: str
    action: str
    reason: str


class ModelRiskSummary(BaseModel):
    code: str
    title: str
    description: str
    risk_level: str
    suggested_action: str


class ValidateExecutionResponse(BaseModel):
    execution_request_id: UUID
    decision: str
    risk_score: int
    risk_level: str
    triggered_rules: list[TriggeredRuleSummary]
    policy_violations: list[PolicyViolationSummary]
    model_risks: list[ModelRiskSummary]
    recommendations: list[str]
    explanation: str
    scan_id: UUID
    dataset_id: UUID
    model_id: UUID
    model_name: str
    execution_purpose: str
    validated_at: datetime

    @field_validator("decision")
    @classmethod
    def validate_decision(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in DECISIONS:
            raise ValueError(f"decision must be one of: {', '.join(sorted(DECISIONS))}")
        return normalized


class ExecutionResultSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    decision: str | None
    risk_score: int | None
    risk_level: str | None
    reason_codes: list[str] = Field(default_factory=list)
    status: str
    created_at: datetime


class ExecutionRequestSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    file_id: UUID
    scan_id: UUID | None
    compliance_model_id: UUID | None
    execution_purpose: str | None
    model_name: str | None
    model_provider: str | None
    status: str
    created_at: datetime
    execution_result: ExecutionResultSummary | None = None


class ExecutionRequestListResponse(BaseModel):
    items: list[ExecutionRequestSummary]
    total: int
    limit: int
    offset: int


class ExecutionRequestDetailResponse(ExecutionRequestSummary):
    evaluation_summary: dict[str, Any] | None = None
    recommendations: list[str] = Field(default_factory=list)


class ExecutionStatusResponse(BaseModel):
    execution_request_id: UUID
    status: str
    decision: str | None
    risk_score: int | None
    risk_level: str | None
    can_start: bool
    requires_acknowledgement: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    warning_reasons: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explanation: str | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by_user_id: UUID | None = None
    started_at: datetime | None = None


class StartExecutionResponse(BaseModel):
    execution_request_id: UUID
    status: str
    decision: str
    message: str
    started_at: datetime


class AcknowledgeWarningRequest(BaseModel):
    acknowledgement_note: str | None = Field(default=None, max_length=2000)


class AcknowledgeWarningResponse(BaseModel):
    execution_request_id: UUID
    status: str
    decision: str
    acknowledged_at: datetime
    acknowledged_by_user_id: UUID
    message: str
    can_start: bool

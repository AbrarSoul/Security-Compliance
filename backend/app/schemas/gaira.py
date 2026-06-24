"""Pydantic schemas for GAIRA APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class GairaModuleSummary(BaseModel):
    key: str
    title: str
    question_count: int = 0


class GairaFrameworkResponse(BaseModel):
    version: str | None
    modules: list[GairaModuleSummary]


class GairaModuleDetailResponse(BaseModel):
    key: str
    title: str
    version: str | None = None
    overview: str | None = None
    metadata_fields: list[dict] = Field(default_factory=list)
    steps: list[dict] = Field(default_factory=list)
    questions: list[dict] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class AIApplicationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=128)
    company: str | None = None
    department: str | None = None
    owner_name: str | None = None
    purpose: str | None = None
    audience: str | None = None
    scope_includes: str | None = None
    scope_excludes: str | None = None
    technology_description: str | None = None
    ai_provider: str | None = None
    compliance_model_id: UUID | None = None
    metadata_json: dict | None = None


class AIApplicationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=128)
    company: str | None = None
    department: str | None = None
    owner_name: str | None = None
    purpose: str | None = None
    audience: str | None = None
    scope_includes: str | None = None
    scope_excludes: str | None = None
    technology_description: str | None = None
    ai_provider: str | None = None
    compliance_model_id: UUID | None = None
    ai_act_category: str | None = None
    risk_level: str | None = None
    deployed_at: datetime | None = None
    next_assessment_at: datetime | None = None
    is_active: bool | None = None
    metadata_json: dict | None = None


class AIApplicationResponse(BaseModel):
    id: UUID
    name: str
    code: str | None
    company: str | None
    department: str | None
    owner_name: str | None
    purpose: str | None
    audience: str | None
    scope_includes: str | None
    scope_excludes: str | None
    technology_description: str | None
    ai_provider: str | None
    compliance_model_id: UUID | None
    ai_act_category: str | None
    risk_level: str | None
    gaira_status: str
    compliance_check_status: str
    dpia_status: str
    deployed_at: datetime | None
    next_assessment_at: datetime | None
    is_active: bool
    metadata_json: dict | None
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIApplicationListResponse(BaseModel):
    items: list[AIApplicationResponse]
    total: int
    limit: int
    offset: int


class StartAssessmentRequest(BaseModel):
    assessment_type: str
    scan_id: UUID | None = None


class UpdateAnswersRequest(BaseModel):
    answers: dict
    merge: bool = True


class SubmitAssessmentRequest(BaseModel):
    overall_risk_level: str | None = None
    proceed_decision: str | None = None
    decision_comments: str | None = None


class GairaAssessmentResponse(BaseModel):
    id: UUID
    application_id: UUID
    assessment_type: str
    status: str
    framework_version: str | None
    current_step: str | None
    answers_json: dict
    computed_json: dict | None
    overall_risk_level: str | None
    proceed_decision: str | None
    decision_comments: str | None
    scan_id: UUID | None
    created_by_user_id: UUID | None
    decision_by_user_id: UUID | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GairaAssessmentListResponse(BaseModel):
    items: list[GairaAssessmentResponse]
    total: int


class RoaiaRow(BaseModel):
    id: str
    name: str
    purpose: str | None = None
    owner_name: str | None = None
    audience: str | None = None
    ai_provider: str | None = None
    technology_description: str | None = None
    ai_act_category: str | None = None
    compliance_check_status: str
    dpia_status: str
    gaira_status: str
    risk_level: str | None = None
    deployed_at: datetime | None = None
    next_assessment_at: datetime | None = None
    latest_assessment_id: str | None = None
    latest_assessment_type: str | None = None


class RoaiaListResponse(BaseModel):
    items: list[RoaiaRow]
    total: int

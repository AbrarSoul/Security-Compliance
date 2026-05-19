from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class GuardPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    metadata: dict[str, Any] | None = None


class GuardOutputRequest(BaseModel):
    output: str = Field(..., min_length=1)
    prompt_scan_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class GuardDecisionDetail(BaseModel):
    decision: str
    risk_score: int
    risk_level: str
    source: str
    reasons: list[str]


class GuardResultResponse(BaseModel):
    allowed: bool
    decision: str
    risk_score: int
    risk_level: str
    execution_request_id: UUID
    session_id: UUID | None = None
    prompt_scan_id: UUID | None = None
    output_scan_id: UUID | None = None
    interrupted: bool
    execution_status: str | None = None
    blocking_reasons: list[str]
    warning_reasons: list[str]
    recommendations: list[str]
    masked_content: str | None = None
    redacted_content: str | None = None
    scan_decision: GuardDecisionDetail | None = None
    rule_decision: GuardDecisionDetail | None = None
    policy_decision: GuardDecisionDetail | None = None
    triggered_rules: list[dict[str, Any]] = Field(default_factory=list)
    policy_violations: list[dict[str, Any]] = Field(default_factory=list)


class GuardActionSummary(BaseModel):
    id: UUID
    enforcement_type: str
    decision: str
    action_taken: str
    source: str
    created_at: datetime


class GuardStatusResponse(BaseModel):
    execution_request_id: UUID
    status: str
    decision: str | None
    can_continue: bool
    guard_actions: list[GuardActionSummary]

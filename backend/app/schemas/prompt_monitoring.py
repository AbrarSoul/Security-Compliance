from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScanPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    session_id: UUID | None = None
    execution_request_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class PromptFindingResponse(BaseModel):
    finding_type: str
    severity: str
    message: str
    matched_span: str | None = None
    masked_span: str | None = None
    suggested_decision: str | None = None
    evidence: dict[str, Any] | None = None


class ScanPromptResponse(BaseModel):
    scan_id: UUID
    decision: str
    risk_score: int
    risk_level: str
    can_proceed: bool
    findings: list[PromptFindingResponse]
    masked_prompt: str
    blocking_reasons: list[str]
    warning_reasons: list[str]
    recommendations: list[str]
    prompt_hash: str
    session_id: UUID | None = None


class PromptScanDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_id: UUID | None
    execution_request_id: UUID | None
    prompt_hash: str
    content_length: int
    decision: str
    risk_score: int
    risk_level: str
    findings: list[PromptFindingResponse]
    masked_prompt: str | None
    blocking_reasons: list[str]
    warning_reasons: list[str]
    recommendations: list[str]
    metadata_json: dict[str, Any] | None
    scanned_at: datetime
    can_proceed: bool

    model_config = {"from_attributes": True}


class PromptScanListResponse(BaseModel):
    items: list[PromptScanDetailResponse]
    total: int
    limit: int
    offset: int

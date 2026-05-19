from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ScanOutputRequest(BaseModel):
    output: str = Field(..., min_length=1)
    session_id: UUID | None = None
    execution_request_id: UUID | None = None
    prompt_scan_id: UUID | None = None
    metadata: dict[str, Any] | None = None


class OutputFindingResponse(BaseModel):
    finding_type: str
    severity: str
    message: str
    matched_span: str | None = None
    masked_span: str | None = None
    suggested_decision: str | None = None
    evidence: dict[str, Any] | None = None


class ScanOutputResponse(BaseModel):
    scan_id: UUID
    decision: str
    risk_score: int
    risk_level: str
    can_display: bool
    findings: list[OutputFindingResponse]
    masked_output: str
    redacted_output: str
    blocking_reasons: list[str]
    warning_reasons: list[str]
    recommendations: list[str]
    output_hash: str
    session_id: UUID | None = None


class OutputScanDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_id: UUID | None
    execution_request_id: UUID | None
    prompt_scan_id: UUID | None
    output_hash: str
    content_length: int
    decision: str
    risk_score: int
    risk_level: str
    findings: list[OutputFindingResponse]
    masked_output: str | None
    redacted_output: str | None
    blocking_reasons: list[str]
    warning_reasons: list[str]
    recommendations: list[str]
    metadata_json: dict[str, Any] | None
    scanned_at: datetime
    can_display: bool

    model_config = {"from_attributes": True}


class OutputScanListResponse(BaseModel):
    items: list[OutputScanDetailResponse]
    total: int
    limit: int
    offset: int

"""Unified compliance posture API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class FrameworkRefResponse(BaseModel):
    framework: str
    control_id: str


class ComplianceIssueResponse(BaseModel):
    id: str
    title: str
    severity: str
    remediation: str
    source: str
    gap_type: str | None = None
    control_ids: list[str] = Field(default_factory=list)
    framework_refs: list[FrameworkRefResponse] = Field(default_factory=list)
    resource_type: str | None = None
    resource_id: str | None = None


class FrameworkPostureResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    alignment_score: float | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    open_issue_count: int
    open_issues: list[ComplianceIssueResponse] = Field(default_factory=list)
    detail_url: str


class CompliancePostureResponse(BaseModel):
    evaluated_at: str
    last_gap_analysis_at: str | None = None
    frameworks: list[FrameworkPostureResponse]
    disclaimer: str

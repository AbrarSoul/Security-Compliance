"""NIST AI RMF API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class NistControlCatalogItem(BaseModel):
    id: str
    function: str
    category_id: str
    category_title: str | None = None
    text: str
    evidence_type: str
    coverage: str
    modules: list[str] = Field(default_factory=list)
    evaluator: str | None = None
    trustworthiness: list[str] = Field(default_factory=list)
    notes: str | None = None


class NistControlsCatalogResponse(BaseModel):
    version: str
    source: str | None = None
    source_url: str | None = None
    playbook_url: str | None = None
    profile: dict[str, Any]
    trustworthiness_characteristics: list[str]
    control_count: int
    controls: list[NistControlCatalogItem]


class NistControlStatusItem(BaseModel):
    id: str
    function: str
    category_id: str | None = None
    text: str
    evidence_type: str
    coverage: str
    modules: list[str] = Field(default_factory=list)
    trustworthiness: list[str] = Field(default_factory=list)
    status: str
    evidence: list[str] = Field(default_factory=list)
    detail: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class NistFunctionSummary(BaseModel):
    met: int = 0
    partial: int = 0
    not_met: int = 0
    not_assessed: int = 0
    not_applicable: int = 0


class NistProfileSummary(BaseModel):
    total: int
    met: int
    partial: int
    not_met: int
    not_assessed: int
    not_applicable: int
    automated_evaluations: int


class NistCurrentProfileResponse(BaseModel):
    profile_id: str | None = None
    profile_name: str | None = None
    framework_version: str
    evaluated_at: str
    alignment_score: float
    summary: NistProfileSummary
    by_function: dict[str, NistFunctionSummary]
    controls: list[NistControlStatusItem]
    disclaimer: str

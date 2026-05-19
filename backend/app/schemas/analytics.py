"""Analytics API schemas (Sprint 3 Step 7)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    bucket: datetime
    value: float


class CountSeriesPoint(BaseModel):
    bucket: datetime
    count: int


class LabelCount(BaseModel):
    label: str
    count: int


class AnalyticsSummaryResponse(BaseModel):
    violation_events: int = 0
    blocked_executions: int = 0
    policy_violations: int = 0
    prompt_scans_total: int = 0
    prompt_blocked: int = 0
    output_scans_total: int = 0
    output_blocked: int = 0
    avg_prompt_risk: float | None = None
    avg_output_risk: float | None = None
    unread_notifications: int = 0
    scope: str = Field(description="'user' or 'organization'")


class RealtimeViolationItem(BaseModel):
    id: UUID
    event_type: str
    severity: str
    occurred_at: datetime
    user_id: UUID | None
    resource_type: str | None
    resource_id: UUID | None
    payload: dict | None = None


class RealtimeViolationsResponse(BaseModel):
    items: list[RealtimeViolationItem]
    total: int


class TrendSeriesResponse(BaseModel):
    metric: str
    granularity: str
    points: list[CountSeriesPoint]


class RiskTrendResponse(BaseModel):
    granularity: str
    points: list[TimeSeriesPoint]


class PromptMonitoringStatsResponse(BaseModel):
    total_scans: int
    blocked: int
    warned: int
    allowed: int
    decision_breakdown: list[LabelCount]
    avg_risk_score: float | None = None


class OutputLeakageStatsResponse(BaseModel):
    total_scans: int
    blocked: int
    warned: int
    leakage_breakdown: list[LabelCount]
    avg_risk_score: float | None = None


class BlockedExecutionsResponse(BaseModel):
    total_blocked: int
    status_breakdown: list[LabelCount]
    trend: list[CountSeriesPoint]


class HighRiskUserItem(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None
    scan_count: int
    avg_risk_score: float
    blocked_prompts: int


class HighRiskUsersResponse(BaseModel):
    items: list[HighRiskUserItem]


class HighRiskModelItem(BaseModel):
    model_id: UUID
    name: str
    provider: str | None
    execution_count: int
    blocked_count: int


class HighRiskModelsResponse(BaseModel):
    items: list[HighRiskModelItem]


class PolicyViolationTrendResponse(BaseModel):
    total: int
    points: list[CountSeriesPoint]


class AnalyticsDashboardResponse(BaseModel):
    """Combined payload for the monitoring dashboard page."""

    summary: AnalyticsSummaryResponse
    execution_trend: list[CountSeriesPoint]
    risk_trend: list[TimeSeriesPoint]
    violation_trend: list[CountSeriesPoint]
    policy_violation_trend: list[CountSeriesPoint]
    prompt_stats: PromptMonitoringStatsResponse
    output_stats: OutputLeakageStatsResponse
    blocked_executions: BlockedExecutionsResponse
    realtime_violations: list[RealtimeViolationItem]
    high_risk_users: list[HighRiskUserItem]
    high_risk_models: list[HighRiskModelItem]
    guard_actions: list[LabelCount]

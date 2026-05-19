export type AnalyticsScope = "user" | "organization";

export type TimeSeriesPoint = { bucket: string; value: number };
export type CountSeriesPoint = { bucket: string; count: number };
export type LabelCount = { label: string; count: number };

export type AnalyticsSummary = {
  violation_events: number;
  blocked_executions: number;
  policy_violations: number;
  prompt_scans_total: number;
  prompt_blocked: number;
  output_scans_total: number;
  output_blocked: number;
  avg_prompt_risk: number | null;
  avg_output_risk: number | null;
  unread_notifications: number;
  scope: AnalyticsScope;
};

export type RealtimeViolation = {
  id: string;
  event_type: string;
  severity: string;
  occurred_at: string;
  user_id: string | null;
  resource_type: string | null;
  resource_id: string | null;
  payload?: Record<string, unknown> | null;
};

export type PromptMonitoringStats = {
  total_scans: number;
  blocked: number;
  warned: number;
  allowed: number;
  decision_breakdown: LabelCount[];
  avg_risk_score: number | null;
};

export type OutputLeakageStats = {
  total_scans: number;
  blocked: number;
  warned: number;
  leakage_breakdown: LabelCount[];
  avg_risk_score: number | null;
};

export type BlockedExecutionsStats = {
  total_blocked: number;
  status_breakdown: LabelCount[];
  trend: CountSeriesPoint[];
};

export type HighRiskUser = {
  user_id: string;
  email: string;
  full_name: string | null;
  scan_count: number;
  avg_risk_score: number;
  blocked_prompts: number;
};

export type HighRiskModel = {
  model_id: string;
  name: string;
  provider: string | null;
  execution_count: number;
  blocked_count: number;
};

export type AnalyticsDashboard = {
  summary: AnalyticsSummary;
  execution_trend: CountSeriesPoint[];
  risk_trend: TimeSeriesPoint[];
  violation_trend: CountSeriesPoint[];
  policy_violation_trend: CountSeriesPoint[];
  prompt_stats: PromptMonitoringStats;
  output_stats: OutputLeakageStats;
  blocked_executions: BlockedExecutionsStats;
  realtime_violations: RealtimeViolation[];
  high_risk_users: HighRiskUser[];
  high_risk_models: HighRiskModel[];
  guard_actions: LabelCount[];
};

export type AnalyticsFilters = {
  days: number;
  severity: string;
  granularity: "hour" | "day" | "week";
};

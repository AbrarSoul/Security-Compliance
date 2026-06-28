export type FrameworkRef = {
  framework: string;
  control_id: string;
};

export type ComplianceGap = {
  id: string;
  analysis_run_id: string;
  gap_type: string;
  category: string;
  severity: string;
  score: number;
  title: string;
  description: string;
  recommendation: string;
  status: string;
  fingerprint: string;
  resource_type: string | null;
  resource_id: string | null;
  metadata_json: Record<string, unknown> | null;
  framework_refs: FrameworkRef[];
  detected_at: string;
  resolved_at: string | null;
};

export type GapAnalysisRun = {
  id: string;
  triggered_by_user_id: string | null;
  scope: string;
  gaps_found: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary_json: Record<string, unknown> | null;
  started_at: string;
  completed_at: string | null;
};

export type GapDashboard = {
  latest_run: GapAnalysisRun | null;
  open_gaps: ComplianceGap[];
  open_total: number;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
  by_framework: Record<string, number>;
  posture_score: number;
  last_analyzed_at: string | null;
};

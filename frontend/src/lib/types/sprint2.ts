/** Sprint 2 API types */

export interface PolicyThresholds {
  block_below: number;
  warn_below: number;
}

export interface ComplianceRule {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category: string;
  severity: string;
  action: string;
  priority: number;
  condition: Record<string, unknown> | null;
  is_enabled: boolean;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CompliancePolicy {
  id: string;
  name: string;
  description: string | null;
  policy_type: string;
  status: string;
  priority: number;
  thresholds: PolicyThresholds;
  is_active: boolean;
  severity_default: string | null;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
  rules: ComplianceRule[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface TriggeredRuleSummary {
  rule_id: string;
  rule_name: string;
  severity: string;
  action: string;
  reason: string;
  rule_code?: string | null;
}

export interface PolicyViolationSummary {
  policy_id: string;
  policy_name: string;
  policy_type: string;
  action: string;
  reason: string;
}

export interface ModelRiskSummary {
  code: string;
  title: string;
  description: string;
  risk_level: string;
  suggested_action: string;
}

export interface ValidateExecutionResponse {
  execution_request_id: string;
  decision: string;
  risk_score: number;
  risk_level: string;
  triggered_rules: TriggeredRuleSummary[];
  policy_violations: PolicyViolationSummary[];
  model_risks: ModelRiskSummary[];
  recommendations: string[];
  explanation: string;
  scan_id: string;
  dataset_id: string;
  model_id: string;
  model_name: string;
  execution_purpose: string;
  validated_at: string;
}

export interface ExecutionResultSummary {
  id: string;
  decision: string | null;
  risk_score: number | null;
  risk_level: string | null;
  reason_codes: string[];
  status: string;
  created_at: string;
}

export interface ExecutionRequest {
  id: string;
  user_id: string;
  file_id: string;
  scan_id: string | null;
  compliance_model_id: string | null;
  execution_purpose: string | null;
  model_name: string | null;
  model_provider: string | null;
  status: string;
  created_at: string;
  execution_result: ExecutionResultSummary | null;
  evaluation_summary?: Record<string, unknown> | null;
  recommendations?: string[];
}

export interface ExecutionStatus {
  execution_request_id: string;
  status: string;
  decision: string | null;
  risk_score: number | null;
  risk_level: string | null;
  can_start: boolean;
  requires_acknowledgement: boolean;
  blocking_reasons: string[];
  warning_reasons: string[];
  recommendations: string[];
  explanation: string | null;
  acknowledged_at: string | null;
  acknowledged_by_user_id: string | null;
  started_at: string | null;
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  severity: string | null;
  status: string;
  metadata: Record<string, unknown> | null;
  request_id: string | null;
  ip_address: string | null;
  created_at: string;
  actor_email?: string | null;
}

export interface GptLabSyncResult {
  created: number;
  updated: number;
  deactivated: number;
  demos_deactivated: number;
  models_synced: string[];
  skipped: string[];
}

export interface ComplianceModel {
  id: string;
  code: string;
  name: string;
  provider: string | null;
  model_type: string;
  endpoint_url: string | null;
  data_retention_policy: string | null;
  logging_enabled: boolean | null;
  data_leaves_platform: boolean;
  is_approved: boolean;
  is_active: boolean;
  metadata: Record<string, unknown> | null;
  created_by_user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ModelValidationResult {
  id: string;
  scan_id: string;
  model_id: string;
  model_name: string;
  model_type: string;
  provider: string | null;
  decision: string;
  risk_level: string;
  risk_score: number;
  primary_reason: string;
  recommendations: string[];
  risk_checks: Array<{
    code: string;
    title: string;
    description: string;
    risk_level: string;
    suggested_action: string;
  }>;
  detected_types: string[];
  dataset_classification: string | null;
  validated_at: string | null;
  created_at: string;
}

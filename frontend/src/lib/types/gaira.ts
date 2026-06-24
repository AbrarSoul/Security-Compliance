/** GAIRA API types */

export interface GairaModuleSummary {
  key: string;
  title: string;
  question_count: number;
}

export interface GairaFramework {
  version: string | null;
  modules: GairaModuleSummary[];
}

export interface GairaQuestion {
  id: string;
  text: string;
  step_id?: string;
  answer_type?: string;
  explanation?: string | null;
  options?: string[];
}

export interface GairaStep {
  id: string;
  title: string;
  instruction?: string | null;
}

export interface GairaModuleDetail {
  key: string;
  title: string;
  version?: string | null;
  overview?: string | null;
  steps: GairaStep[];
  questions: GairaQuestion[];
}

export interface AIApplication {
  id: string;
  name: string;
  code: string | null;
  company: string | null;
  department: string | null;
  owner_name: string | null;
  purpose: string | null;
  audience: string | null;
  scope_includes: string | null;
  scope_excludes: string | null;
  technology_description: string | null;
  ai_provider: string | null;
  compliance_model_id: string | null;
  ai_act_category: string | null;
  risk_level: string | null;
  gaira_status: string;
  compliance_check_status: string;
  dpia_status: string;
  deployed_at: string | null;
  next_assessment_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface GairaAnswer {
  value?: string | boolean | number | null;
  description?: string;
  source?: string;
  note?: string;
  flagged?: boolean;
  second_line_reviewer?: string;
  second_line_comment?: string;
}

export interface GairaComputed {
  risk_level?: string | null;
  recommended_module?: string | null;
  proceed_recommendation?: string | null;
  flags?: string[];
  details?: Record<string, unknown>;
}

export interface GairaAssessment {
  id: string;
  application_id: string;
  assessment_type: string;
  status: string;
  framework_version: string | null;
  current_step: string | null;
  answers_json: Record<string, GairaAnswer>;
  computed_json: GairaComputed | null;
  overall_risk_level: string | null;
  proceed_decision: string | null;
  decision_comments: string | null;
  scan_id: string | null;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoaiaRow {
  id: string;
  name: string;
  purpose: string | null;
  owner_name: string | null;
  audience: string | null;
  ai_provider: string | null;
  technology_description: string | null;
  ai_act_category: string | null;
  compliance_check_status: string;
  dpia_status: string;
  gaira_status: string;
  risk_level: string | null;
  deployed_at: string | null;
  next_assessment_at: string | null;
  latest_assessment_id: string | null;
  latest_assessment_type: string | null;
}

export const ASSESSMENT_TYPE_LABELS: Record<string, string> = {
  ai_risk_levels: "AI Risk Levels (triage)",
  gaira_light: "GAIRA Light",
  gaira_comprehensive: "GAIRA Comprehensive",
  ai_act_check: "AI Act Check",
  compliance_check: "Compliance Check",
};

export const RISK_LEVEL_OPTIONS = [
  "insignificant",
  "low",
  "medium",
  "high",
  "very_high",
] as const;

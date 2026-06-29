export type NistControlStatus =
  | "met"
  | "partial"
  | "not_met"
  | "not_assessed"
  | "not_applicable";

export type NistFindingKind =
  | "satisfied"
  | "violation"
  | "alignment_gap"
  | "improvement"
  | "unchecked"
  | "out_of_scope";

export type NistComplianceStatus = "compliant" | "attention_needed" | "non_compliant";

export interface NistControlCatalogItem {
  id: string;
  function: string;
  category_id: string;
  category_title?: string;
  text: string;
  evidence_type: string;
  coverage: string;
  modules: string[];
  evaluator?: string | null;
  trustworthiness: string[];
  notes?: string | null;
}

export interface NistControlsCatalog {
  version: string;
  source?: string;
  source_url?: string;
  playbook_url?: string;
  profile: {
    id: string;
    name: string;
    description: string;
    type: string;
  };
  trustworthiness_characteristics: string[];
  control_count: number;
  controls: NistControlCatalogItem[];
}

export interface NistControlStatusItem {
  id: string;
  function: string;
  category_id?: string;
  text: string;
  evidence_type: string;
  coverage: string;
  modules: string[];
  trustworthiness: string[];
  status: NistControlStatus;
  finding_kind: NistFindingKind;
  evidence: string[];
  detail: Record<string, unknown>;
  notes?: string | null;
}

export interface NistFunctionSummary {
  met: number;
  partial: number;
  not_met: number;
  not_assessed: number;
  not_applicable: number;
  violations?: number;
  alignment_gaps?: number;
}

export interface NistCurrentProfile {
  profile_id?: string;
  profile_name?: string;
  framework_version: string;
  evaluated_at: string;
  alignment_score: number;
  compliance_status: NistComplianceStatus;
  summary: NistFunctionSummary & {
    total: number;
    automated_evaluations: number;
    violations: number;
    alignment_gaps: number;
    evaluated_total: number;
    progress_total: number;
    base_score: number;
    violation_deduction: number;
  };
  by_function: Record<string, NistFunctionSummary>;
  controls: NistControlStatusItem[];
  disclaimer: string;
}

export const NIST_FUNCTIONS = ["GOVERN", "MAP", "MEASURE", "MANAGE"] as const;

export const NIST_STATUS_LABELS: Record<NistControlStatus, string> = {
  met: "Satisfied",
  partial: "Partial",
  not_met: "Not met",
  not_assessed: "Not checked yet",
  not_applicable: "Out of scope",
};

export const NIST_FINDING_KIND_LABELS: Record<NistFindingKind, string> = {
  satisfied: "Satisfied",
  violation: "Violation",
  alignment_gap: "Setup gap",
  improvement: "Improve",
  unchecked: "Not checked",
  out_of_scope: "Out of scope",
};

export const NIST_COMPLIANCE_STATUS_LABELS: Record<NistComplianceStatus, string> = {
  compliant: "Compliant",
  attention_needed: "Setup in progress",
  non_compliant: "Action needed",
};

export const NIST_STATUS_COLORS: Record<NistControlStatus, string> = {
  met: "text-accent-green",
  partial: "text-accent-amber",
  not_met: "text-accent-red",
  not_assessed: "text-text-muted",
  not_applicable: "text-text-muted",
};

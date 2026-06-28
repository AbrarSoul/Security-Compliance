export type NistControlStatus =
  | "met"
  | "partial"
  | "not_met"
  | "not_assessed"
  | "not_applicable";

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
}

export interface NistCurrentProfile {
  profile_id?: string;
  profile_name?: string;
  framework_version: string;
  evaluated_at: string;
  alignment_score: number;
  summary: NistFunctionSummary & {
    total: number;
    automated_evaluations: number;
  };
  by_function: Record<string, NistFunctionSummary>;
  controls: NistControlStatusItem[];
  disclaimer: string;
}

export const NIST_FUNCTIONS = ["GOVERN", "MAP", "MEASURE", "MANAGE"] as const;

export const NIST_STATUS_LABELS: Record<NistControlStatus, string> = {
  met: "Met",
  partial: "Partial",
  not_met: "Not met",
  not_assessed: "Not assessed",
  not_applicable: "N/A",
};

export const NIST_STATUS_COLORS: Record<NistControlStatus, string> = {
  met: "text-accent-green",
  partial: "text-accent-amber",
  not_met: "text-accent-red",
  not_assessed: "text-text-muted",
  not_applicable: "text-text-muted",
};

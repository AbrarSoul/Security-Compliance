export type FrameworkRef = {
  framework: string;
  control_id: string;
};

export type ComplianceIssue = {
  id: string;
  title: string;
  severity: string;
  remediation: string;
  source: string;
  gap_type: string | null;
  control_ids: string[];
  framework_refs: FrameworkRef[];
  resource_type: string | null;
  resource_id: string | null;
};

export type FrameworkPosture = {
  id: string;
  name: string;
  description: string;
  status: string;
  alignment_score: number | null;
  summary: Record<string, number>;
  open_issue_count: number;
  open_issues: ComplianceIssue[];
  detail_url: string;
};

export type CompliancePosture = {
  evaluated_at: string;
  last_gap_analysis_at: string | null;
  frameworks: FrameworkPosture[];
  disclaimer: string;
};

export const FRAMEWORK_LABELS: Record<string, string> = {
  nist_ai_rmf: "NIST AI RMF",
  internal_guardrails: "Internal guardrails",
  gaira: "GAIRA governance",
};

export const POSTURE_STATUS_LABELS: Record<string, string> = {
  met: "Compliant",
  partial: "Partial",
  not_met: "Non-compliant",
  not_assessed: "Not assessed",
};

import type { StatusVariant } from "@/lib/utils";

export function postureStatusVariant(status: string): StatusVariant {
  switch (status) {
    case "met":
      return "success";
    case "partial":
      return "warning";
    case "not_met":
      return "danger";
    default:
      return "neutral";
  }
}

import type {
  NistComplianceStatus,
  NistControlStatus,
  NistControlStatusItem,
  NistCurrentProfile,
  NistFindingKind,
} from "@/lib/types/nistAiRmf";
import { NIST_COMPLIANCE_STATUS_LABELS } from "@/lib/types/nistAiRmf";

export const NIST_FUNCTION_INFO: Record<
  string,
  { title: string; description: string }
> = {
  GOVERN: {
    title: "Govern",
    description: "Policies, roles, and oversight for AI risk",
  },
  MAP: {
    title: "Map",
    description: "AI use cases inventoried and risks identified",
  },
  MEASURE: {
    title: "Measure",
    description: "Risks detected through scans, monitoring, and checks",
  },
  MANAGE: {
    title: "Manage",
    description: "Risks responded to via blocks, gaps, and remediation",
  },
};

export const NIST_STATUS_INFO: Record<
  NistControlStatus,
  { label: string; short: string; description: string }
> = {
  met: {
    label: "Satisfied",
    short: "Satisfied",
    description: "Platform data shows this requirement is in place.",
  },
  partial: {
    label: "Partially satisfied",
    short: "Partial",
    description: "Some evidence exists, but more work is needed.",
  },
  not_met: {
    label: "Not met",
    short: "Not met",
    description: "This requirement is not yet in place — often because setup is incomplete.",
  },
  not_assessed: {
    label: "Not checked yet",
    short: "Not checked",
    description:
      "ComplianceGuard does not automatically verify this yet. It may need manual review outside the platform.",
  },
  not_applicable: {
    label: "Out of scope",
    short: "N/A",
    description:
      "This requirement is outside what ComplianceGuard tracks for your AI operations profile.",
  },
};

export const NIST_FINDING_KIND_INFO: Record<
  NistFindingKind,
  { label: string; short: string; description: string; badgeVariant: "danger" | "warning" | "success" | "neutral" }
> = {
  satisfied: {
    label: "Satisfied",
    short: "OK",
    description: "No issue detected for this requirement.",
    badgeVariant: "success",
  },
  violation: {
    label: "Violation",
    short: "Violation",
    description:
      "Active policy breach — something in use (models, apps, monitoring) does not meet this requirement.",
    badgeVariant: "danger",
  },
  alignment_gap: {
    label: "Setup gap",
    short: "Setup gap",
    description:
      "Requirement not met yet, but no active breach detected — typically incomplete platform setup or maturity.",
    badgeVariant: "warning",
  },
  improvement: {
    label: "Improve",
    short: "Improve",
    description: "Partial progress — continue strengthening this area.",
    badgeVariant: "warning",
  },
  unchecked: {
    label: "Not checked yet",
    short: "Not checked",
    description: "Not automatically verified by the platform.",
    badgeVariant: "neutral",
  },
  out_of_scope: {
    label: "Out of scope",
    short: "N/A",
    description: "Outside what ComplianceGuard tracks for this profile.",
    badgeVariant: "neutral",
  },
};

const MODULE_ACTIONS: Record<string, { label: string; href: string }> = {
  gaira: { label: "Open GAIRA inventory", href: "/gaira" },
  policies: { label: "Review policies", href: "/policies" },
  rules: { label: "Review rules", href: "/rules" },
  scans: { label: "Run dataset scans", href: "/scans" },
  models: { label: "Review model registry", href: "/models" },
  guard: { label: "View execution guard", href: "/executions" },
  execution: { label: "View executions", href: "/executions" },
  gaps: { label: "Run gap analysis", href: "/gaps" },
  audit: { label: "View audit activity", href: "/analytics" },
  rbac: { label: "Manage user roles", href: "/users" },
};

export type NistBarSegmentKey = "met" | "partial" | "violation";

export const NIST_BAR_SEGMENT_INFO: Record<
  NistBarSegmentKey,
  { label: string; color: string }
> = {
  met: { label: "Satisfied", color: "bg-flag-success" },
  partial: { label: "Partially satisfied", color: "bg-flag-warning" },
  violation: { label: "Violation", color: "bg-flag-danger" },
};

export function buildProfileHeadline(
  alignmentScore: number,
  violations: number,
  setupGaps: number,
): string {
  if (violations > 0 && alignmentScore >= 80) {
    return "Mostly aligned";
  }
  if (violations > 0 && alignmentScore >= 50) {
    return "Review open issues";
  }
  if (violations > 0) {
    return "Needs attention";
  }
  if (alignmentScore >= 85) {
    return "Well aligned";
  }
  if (alignmentScore >= 60) {
    return "On track";
  }
  if (setupGaps > 0) {
    return "Setup in progress";
  }
  return "Getting started";
}

export interface NistProfileInsights {
  profileHeadline: string;
  complianceLabel: string;
  complianceSummary: string;
  readinessLabel: string;
  readinessSummary: string;
  scoreExplanation: string;
  automatedCount: number;
  manualOrPendingCount: number;
  violationCount: number;
  setupGapCount: number;
  actionItems: NistActionItem[];
  breakdown: Array<{ key: NistBarSegmentKey; count: number; percent: number }>;
}

export interface NistActionItem {
  control: NistControlStatusItem;
  priority: "high" | "medium";
  reason: string;
  action?: { label: string; href: string };
}

export function displayFindingKind(control: NistControlStatusItem): NistFindingKind {
  return control.finding_kind ?? "satisfied";
}

export function controlDisplayInfo(control: NistControlStatusItem): {
  label: string;
  short: string;
  description: string;
  badgeVariant: "danger" | "warning" | "success" | "neutral";
} {
  const kind = displayFindingKind(control);
  if (kind === "violation" || kind === "alignment_gap" || kind === "improvement") {
    return NIST_FINDING_KIND_INFO[kind];
  }
  if (control.status === "not_assessed") {
    return NIST_FINDING_KIND_INFO.unchecked;
  }
  if (control.status === "not_applicable") {
    return NIST_FINDING_KIND_INFO.out_of_scope;
  }
  const statusInfo = NIST_STATUS_INFO[control.status];
  return {
    ...statusInfo,
    badgeVariant:
      control.status === "met" ? "success" : control.status === "partial" ? "warning" : "warning",
  };
}

export function buildProfileInsights(profile: NistCurrentProfile): NistProfileInsights {
  const { summary } = profile;
  const total = summary.total;
  const satisfied = summary.met;
  const partial = summary.partial;
  const notMet = summary.not_met;
  const notChecked = summary.not_assessed;
  const outOfScope = summary.not_applicable;
  const violations = summary.violations ?? 0;
  const setupGaps = summary.alignment_gaps ?? 0;

  const complianceLabel =
    NIST_COMPLIANCE_STATUS_LABELS[profile.compliance_status ?? "attention_needed"];
  const profileHeadline = buildProfileHeadline(
    profile.alignment_score,
    violations,
    setupGaps,
  );

  const complianceSummary =
    violations > 0
      ? `${violations} active violation${violations === 1 ? "" : "s"} to resolve — overall alignment is ${profile.alignment_score}%`
      : setupGaps > 0 || partial > 0
        ? `No violations · ${setupGaps} setup gap${setupGaps === 1 ? "" : "s"} · ${partial} partial`
        : "No violations or setup gaps detected";

  const readinessSummary = [
    `${satisfied} satisfied`,
    violations > 0 ? `${violations} violation${violations === 1 ? "" : "s"}` : null,
    setupGaps > 0 ? `${setupGaps} setup gap${setupGaps === 1 ? "" : "s"}` : null,
    partial > 0 ? `${partial} partial` : null,
    notMet > 0 && setupGaps !== notMet ? `${notMet} not met` : null,
    notChecked > 0 ? `${notChecked} not checked yet` : null,
    outOfScope > 0 ? `${outOfScope} out of scope` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  const evaluatedTotal = summary.evaluated_total ?? summary.met + summary.partial + summary.not_met;
  const progressTotal = summary.progress_total ?? summary.met + summary.partial;
  const baseScore = summary.base_score;
  const violationDeduction = summary.violation_deduction ?? 0;

  const scoreExplanation =
    progressTotal > 0
      ? `Alignment is ${profile.alignment_score}% from ${progressTotal} requirements with progress ` +
        `(${summary.met} satisfied, ${summary.partial} partial) — not checked against all ${total} catalog items. ` +
        `Base ${baseScore}%` +
        (violationDeduction > 0
          ? `, minus ${violationDeduction}% for ${violations} violation${violations === 1 ? "" : "s"} ` +
            `(deducted from ${evaluatedTotal} auto-checked items).`
          : ". No violation deduction.")
      : `Alignment is 0% — no satisfied or partial requirements yet (${evaluatedTotal} auto-checked, ` +
        `${summary.not_met} not met). Setup gaps do not use the 72-item denominator.`;

  const actionItems = profile.controls
    .filter((c) => c.finding_kind === "violation" || c.finding_kind === "alignment_gap")
    .map((control) => ({
      control,
      priority: control.finding_kind === "violation" ? ("high" as const) : ("medium" as const),
      reason: controlReason(control),
      action: suggestAction(control),
    }))
    .concat(
      profile.controls
        .filter((c) => c.finding_kind === "improvement")
        .map((control) => ({
          control,
          priority: "medium" as const,
          reason: controlReason(control),
          action: suggestAction(control),
        }))
    )
    .sort((a, b) => (a.priority === b.priority ? 0 : a.priority === "high" ? -1 : 1));

  const barSegments: NistBarSegmentKey[] = ["met", "partial", "violation"];
  const barCounts: Record<NistBarSegmentKey, number> = {
    met: satisfied,
    partial,
    violation: violations,
  };
  const barTotal = barSegments.reduce((sum, key) => sum + barCounts[key], 0);
  const breakdown = barSegments
    .map((key) => ({
      key,
      count: barCounts[key],
      percent: barTotal > 0 ? (barCounts[key] / barTotal) * 100 : 0,
    }))
    .filter((item) => item.count > 0);

  let readinessLabel = "Building alignment";
  if (violations === 0 && setupGaps === 0 && partial === 0 && satisfied > 0) {
    readinessLabel = "Strong alignment";
  } else if (violations === 0 && satisfied >= total * 0.4) {
    readinessLabel = "On track";
  } else if (violations > 0) {
    readinessLabel = "Fix violations";
  } else if (setupGaps > 0) {
    readinessLabel = "Setup in progress";
  }

  return {
    profileHeadline,
    complianceLabel,
    complianceSummary,
    readinessLabel,
    readinessSummary,
    scoreExplanation,
    automatedCount: summary.automated_evaluations,
    manualOrPendingCount: notChecked + outOfScope,
    violationCount: violations,
    setupGapCount: setupGaps,
    actionItems,
    breakdown,
  };
}

export function controlReason(control: NistControlStatusItem): string {
  if (control.evidence.length > 0) {
    return control.evidence.join(" · ");
  }
  const reason = control.detail?.reason;
  if (typeof reason === "string" && reason.trim()) {
    return reason;
  }
  return controlDisplayInfo(control).description;
}

export function suggestAction(
  control: NistControlStatusItem
): { label: string; href: string } | undefined {
  if (
    control.finding_kind !== "violation" &&
    control.finding_kind !== "alignment_gap" &&
    control.finding_kind !== "improvement"
  ) {
    return undefined;
  }
  for (const mod of control.modules) {
    const action = MODULE_ACTIONS[mod.toLowerCase()];
    if (action) return action;
  }
  if (control.function === "MANAGE") {
    return MODULE_ACTIONS.gaps;
  }
  return undefined;
}

export function statusBarColor(status: NistControlStatus): string {
  switch (status) {
    case "met":
      return "bg-flag-success";
    case "partial":
      return "bg-flag-warning";
    case "not_met":
      return "bg-flag-warning";
    case "not_assessed":
      return "bg-border";
    case "not_applicable":
      return "bg-background-tertiary";
    default:
      return "bg-border";
  }
}

export function findingKindBarColor(kind: NistFindingKind): string {
  switch (kind) {
    case "violation":
      return "bg-flag-danger";
    case "alignment_gap":
    case "improvement":
      return "bg-flag-warning";
    case "satisfied":
      return "bg-flag-success";
    default:
      return "bg-border";
  }
}

export function complianceStatusVariant(
  status: NistComplianceStatus
): "success" | "warning" | "danger" {
  switch (status) {
    case "compliant":
      return "success";
    case "non_compliant":
      return "danger";
    default:
      return "warning";
  }
}

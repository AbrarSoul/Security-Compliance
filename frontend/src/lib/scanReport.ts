import type { ComplianceScore, ScanFinding, Recommendation } from "@/lib/types";
import { formatBytes, statusLabel } from "@/lib/utils";

export const FINDING_TYPE_LABELS: Record<string, string> = {
  email: "Email addresses",
  phone: "Phone numbers",
  password: "Plaintext credentials",
  api_key: "API keys or secrets",
  name: "Personal names",
  sensitive_field: "Sensitive personal data",
};

export const FINDING_IMPACT: Record<string, string> = {
  email: "Direct identifiers that may fall under privacy regulations (GDPR, CCPA).",
  phone: "Contact information that can identify individuals when combined with other fields.",
  password: "Stored credentials pose immediate account takeover risk if exposed.",
  api_key: "Secrets in data files can grant unauthorized access to external systems.",
  name: "Personal names are PII and may require consent or anonymization.",
  sensitive_field: "Column naming or values suggest regulated or confidential personal data.",
};

export const CLASSIFICATION_DESCRIPTIONS: Record<string, string> = {
  public: "No significant sensitive patterns detected in the sampled data.",
  internal: "Low-sensitivity identifiers found; limit distribution to internal teams.",
  confidential: "Personal or contact data detected; apply access controls and encryption.",
  restricted: "High-risk secrets or credentials detected; restrict access immediately.",
};

export const COMPLIANCE_VERDICT: Record<string, { title: string; tone: string }> = {
  compliant: {
    title: "Dataset appears compliant",
    tone: "No material compliance issues were found in the scanned sample.",
  },
  risky: {
    title: "Dataset needs review",
    tone: "Some sensitive patterns were detected. Review findings before sharing or processing.",
  },
  non_compliant: {
    title: "Dataset is not compliant",
    tone: "Critical or high-risk sensitive data was detected. Remediate before wider use.",
  },
};

export function findingTypeLabel(type: string): string {
  if (type.startsWith("gap_")) {
    const name = type.slice(4).replace(/_/g, " ");
    return `Missing: ${name}`;
  }
  if (type.startsWith("rule_")) {
    const name = type.slice(5).replace(/_/g, " ");
    const labels: Record<string, string> = {
      "dq missing values": "Missing values in dataset",
      "dq duplicate rows": "Duplicate rows in dataset",
      "dq empty dataset": "Empty dataset",
      "col password field": "Password column detected",
      "col ssn field": "SSN / national ID column detected",
      "col email field": "Email column detected",
      "text api key pattern": "API key or secret pattern",
      "text password assignment": "Hardcoded password in text",
      "text email present": "Email addresses in text",
      "log auth failures": "Authentication failures in log",
      "log errors present": "Error entries in log",
    };
    return labels[name] ?? name.charAt(0).toUpperCase() + name.slice(1);
  }
  return FINDING_TYPE_LABELS[type] ?? type.replace(/_/g, " ");
}

export function isComplianceGapFinding(finding: ScanFinding): boolean {
  return (
    finding.finding_type.startsWith("gap_") ||
    finding.evidence?.finding_kind === "compliance_gap"
  );
}

export function gapPriorityLabel(severity: string): string {
  const level = severity?.toLowerCase() ?? "medium";
  if (level === "critical") return "Critical priority";
  if (level === "high") return "High priority";
  if (level === "medium") return "Medium priority";
  return "Low priority";
}

export function formatComplianceGapExplanation(
  finding: ScanFinding
): string | null {
  const raw = finding.evidence?.explanation;
  if (raw == null) return null;
  const text = String(raw);
  if (/only\s+0\s+keyword/i.test(text)) {
    const terms = finding.evidence?.expected_terms;
    if (Array.isArray(terms) && terms.length > 0) {
      const examples = terms.slice(0, 4).map((t) => `"${String(t)}"`).join(", ");
      return (
        `Required policy content is missing from this document. ` +
        `None of the expected phrases were found (e.g. ${examples}).`
      );
    }
    return "Required policy content is missing from this document.";
  }
  return text;
}

export function isRuleBasedFinding(finding: ScanFinding): boolean {
  return (
    finding.finding_type.startsWith("rule_") ||
    finding.evidence?.finding_kind === "risk"
  );
}

export function findingImpact(type: string): string | null {
  return FINDING_IMPACT[type] ?? null;
}

export function formatMatchRate(rate: number | null | undefined): string {
  if (rate == null) return "—";
  const pct = rate * 100;
  if (pct >= 80) return `${pct.toFixed(1)}% of sampled rows (high confidence)`;
  if (pct >= 30) return `${pct.toFixed(1)}% of sampled rows (moderate confidence)`;
  return `${pct.toFixed(1)}% of sampled rows (low prevalence)`;
}

export function riskBandLabel(score: number | null | undefined): string {
  if (score == null) return "Not scored";
  if (score <= 30) return "Low risk";
  if (score <= 60) return "Moderate risk";
  return "High risk";
}

export function scanDurationMs(started: string | null, completed: string | null): string | null {
  if (!started || !completed) return null;
  const ms = new Date(completed).getTime() - new Date(started).getTime();
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

export function buildDatasetScopeLabel(meta: {
  file_type?: string;
  size_bytes?: number;
  row_count?: number | null;
  column_count?: number | null;
}): string {
  const parts: string[] = [];
  if (meta.file_type) parts.push(meta.file_type.toUpperCase());
  if (meta.row_count != null) parts.push(`${meta.row_count.toLocaleString()} rows`);
  if (meta.column_count != null) parts.push(`${meta.column_count} columns`);
  if (meta.size_bytes != null) parts.push(formatBytes(meta.size_bytes));
  return parts.join(" · ") || "Dataset profile unavailable";
}

export function groupFindingsBySeverity(findings: ScanFinding[]): Record<string, ScanFinding[]> {
  const order = ["critical", "high", "medium", "low"];
  const groups: Record<string, ScanFinding[]> = {};
  for (const f of findings) {
    const key = f.severity?.toLowerCase() ?? "medium";
    if (!groups[key]) groups[key] = [];
    groups[key].push(f);
  }
  return Object.fromEntries(order.filter((s) => groups[s]?.length).map((s) => [s, groups[s]]));
}

export function groupRecommendationsByPriority(recs: Recommendation[]): Record<string, Recommendation[]> {
  const order = ["high", "medium", "low"];
  const groups: Record<string, Recommendation[]> = {};
  for (const r of recs) {
    const key = r.priority?.toLowerCase() ?? "medium";
    if (!groups[key]) groups[key] = [];
    groups[key].push(r);
  }
  return Object.fromEntries(order.filter((p) => groups[p]?.length).map((p) => [p, groups[p]]));
}

export function formatFindingReason(reason: string): string {
  const labels: Record<string, string> = {
    credential_like_values_detected: "Values match stored plaintext password patterns",
    password_column_with_credential_like_values:
      "Column name and values indicate stored credentials",
    sensitive_column_name: "Column name indicates sensitive personal data",
    name_pattern_in_values: "Values resemble person names",
    column_name_indicates_password_storage: "Column name suggests password storage",
  };
  return labels[reason] ?? reason.replace(/_/g, " ");
}

export interface FindingLocation {
  index: number;
  preview?: string;
}

const LOCATION_TYPE_LABELS: Record<string, { singular: string; plural: string }> = {
  row: { singular: "Row", plural: "Rows" },
  record: { singular: "Record", plural: "Records" },
  line: { singular: "Line", plural: "Lines" },
  field: { singular: "Field", plural: "Fields" },
};

export function parseFindingLocations(
  evidence: Record<string, unknown> | null | undefined
): { label: string; locations: FindingLocation[]; additionalCount: number } | null {
  if (!evidence) return null;
  const raw = evidence.locations;
  if (!Array.isArray(raw) || raw.length === 0) return null;

  const locationType = String(evidence.location_type ?? "row");
  const labels = LOCATION_TYPE_LABELS[locationType] ?? LOCATION_TYPE_LABELS.row;
  const locations: FindingLocation[] = raw
    .filter((item): item is Record<string, unknown> => !!item && typeof item === "object")
    .map((item) => ({
      index: Number(item.index),
      preview: item.preview != null ? String(item.preview) : undefined,
    }))
    .filter((item) => Number.isFinite(item.index));

  if (!locations.length) return null;

  return {
    label: locations.length === 1 ? labels.singular : labels.plural,
    locations,
    additionalCount: Number(evidence.additional_match_count ?? 0) || 0,
  };
}

export function formatLocationEntry(
  locationType: string,
  index: number,
  columnName?: string | null
): string {
  const labels = LOCATION_TYPE_LABELS[locationType] ?? LOCATION_TYPE_LABELS.row;
  const prefix = `${labels.singular} ${index}`;
  return columnName ? `${prefix}, column '${columnName}'` : prefix;
}

export function scoreContributionSummary(score: ComplianceScore | null | undefined): string | null {
  if (!score?.contributions?.length) return null;
  const top = [...score.contributions].sort((a, b) => b.total_points - a.total_points)[0];
  if (!top) return null;
  return `Primary driver: ${findingTypeLabel(top.finding_type)} in '${top.column_name ?? "unknown"}' (+${top.total_points} pts)`;
}

export function complianceStatusLabel(status: string | null | undefined): string {
  return statusLabel(status);
}

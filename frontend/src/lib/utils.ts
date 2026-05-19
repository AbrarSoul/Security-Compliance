export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function statusLabel(status: string | null | undefined): string {
  if (!status) return "Unknown";
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export type StatusVariant = "success" | "warning" | "danger" | "neutral" | "info";

export function complianceVariant(status: string | null | undefined): StatusVariant {
  switch (status) {
    case "compliant":
      return "success";
    case "risky":
      return "warning";
    case "non_compliant":
      return "danger";
    default:
      return "neutral";
  }
}

export function severityVariant(severity: string): StatusVariant {
  switch (severity?.toLowerCase()) {
    case "critical":
    case "high":
      return "danger";
    case "medium":
      return "warning";
    case "low":
      return "success";
    case "info":
      return "info";
    default:
      return "neutral";
  }
}

export function flagVariant(value: string | null | undefined): StatusVariant {
  switch (value?.toLowerCase()) {
    case "compliant":
    case "allow":
    case "allowed":
    case "approved":
    case "approved_after_warning":
    case "completed":
    case "active":
    case "enabled":
    case "started":
    case "running":
    case "success":
    case "ok":
    case "low":
    case "resolved":
    case "acknowledged":
      return "success";
    case "risky":
    case "warn":
    case "warning":
    case "warning_pending_acknowledgement":
    case "pending":
    case "pending_validation":
    case "pending_acknowledgement":
    case "review":
    case "medium":
    case "investigating":
      return "warning";
    case "non_compliant":
    case "block":
    case "blocked":
    case "interrupted":
    case "failed":
    case "error":
    case "critical":
    case "high":
    case "denied":
    case "rejected":
      return "danger";
    case "info":
    case "queued":
    case "validating":
    case "validated":
    case "scanning":
      return "info";
    case "disabled":
    case "inactive":
    case "draft":
    case "cancelled":
    case "unknown":
    case "n/a":
      return "neutral";
    default:
      return "neutral";
  }
}

export function riskColor(score: number | null | undefined): string {
  if (score == null) return "text-text-muted";
  if (score <= 30) return "text-flag-success";
  if (score <= 60) return "text-flag-warning";
  return "text-flag-danger";
}

export function decisionVariant(decision: string | null | undefined): StatusVariant {
  switch (decision?.toLowerCase()) {
    case "allow":
      return "success";
    case "warn":
      return "warning";
    case "block":
      return "danger";
    default:
      return "neutral";
  }
}

export function riskBgColor(score: number | null | undefined): string {
  if (score == null) return "bg-surface-elevated";
  if (score <= 30) return "bg-flag-success";
  if (score <= 60) return "bg-flag-warning";
  return "bg-flag-danger";
}

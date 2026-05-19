import {
  complianceVariant,
  flagVariant,
  severityVariant,
  statusLabel,
  type StatusVariant,
} from "@/lib/utils";

const variants: Record<StatusVariant, string> = {
  success: "status-success",
  warning: "status-warning",
  danger: "status-danger",
  info: "status-info",
  neutral: "status-neutral",
};

export function Badge({
  children,
  variant = "neutral",
}: {
  children: string;
  variant?: StatusVariant;
}) {
  return <span className={variants[variant]}>{children}</span>;
}

export function ComplianceBadge({ status }: { status: string | null | undefined }) {
  return <Badge variant={complianceVariant(status)}>{statusLabel(status)}</Badge>;
}

export function SeverityBadge({ severity }: { severity: string }) {
  return <Badge variant={severityVariant(severity)}>{severity}</Badge>;
}

/**
 * Generic flag badge — colors any common status string (started, allow, block,
 * enabled, critical, completed, …) by mapping it through `flagVariant`.
 */
export function FlagBadge({ value }: { value: string | null | undefined }) {
  return <Badge variant={flagVariant(value)}>{statusLabel(value)}</Badge>;
}

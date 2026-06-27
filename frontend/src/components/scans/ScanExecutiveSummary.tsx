import type { UploadedFile } from "@/lib/types";
import { Alert } from "@/components/ui/Alert";
import {
  CLASSIFICATION_DESCRIPTIONS,
  COMPLIANCE_VERDICT,
  buildDatasetScopeLabel,
  complianceStatusLabel,
  scanDurationMs,
} from "@/lib/scanReport";
import { complianceVariant } from "@/lib/utils";

export function ScanExecutiveSummary({
  complianceStatus,
  classification,
  findingsCount,
  file,
  startedAt,
  completedAt,
}: {
  complianceStatus: string | null | undefined;
  classification: string | null | undefined;
  findingsCount: number;
  file: UploadedFile | null;
  startedAt: string | null;
  completedAt: string | null;
}) {
  const status = complianceStatus ?? "unknown";
  const verdict = COMPLIANCE_VERDICT[status] ?? {
    title: "Scan complete",
    tone: "Review the findings below.",
  };
  const variant = complianceVariant(status);
  const duration = scanDurationMs(startedAt, completedAt);
  const scope = file
    ? buildDatasetScopeLabel({
        file_type: file.file_type,
        size_bytes: file.size_bytes,
        row_count: file.metadata?.row_count,
        column_count: file.metadata?.column_count,
      })
    : null;

  const alertVariant: "error" | "success" | "info" =
    variant === "success" ? "success" : variant === "danger" ? "error" : "info";

  return (
    <div className="space-y-4">
      <Alert variant={alertVariant}>
        <p className="font-semibold text-text-primary">{verdict.title}</p>
        <p className="mt-1 text-sm">{verdict.tone}</p>
        {classification && CLASSIFICATION_DESCRIPTIONS[classification] && (
          <p className="mt-2 text-sm text-text-muted">{CLASSIFICATION_DESCRIPTIONS[classification]}</p>
        )}
      </Alert>

      <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <SummaryItem label="Compliance" value={complianceStatusLabel(status)} />
        <SummaryItem label="Findings" value={String(findingsCount)} />
        {scope && <SummaryItem label="Dataset" value={scope} />}
        {duration && <SummaryItem label="Scan duration" value={duration} />}
      </dl>

      <p className="text-xs text-text-muted">
        Analysis is sample-based (up to the configured row limit). Absence of a finding does not
        guarantee the full file is free of sensitive data.
      </p>
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-background-tertiary/40 px-3 py-2.5">
      <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</dt>
      <dd className="mt-1 font-medium text-text-primary">{value}</dd>
    </div>
  );
}

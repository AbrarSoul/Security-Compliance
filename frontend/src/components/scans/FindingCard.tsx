import type { ScanFinding } from "@/lib/types";
import { SeverityBadge } from "@/components/ui/Badge";
import {
  findingImpact,
  findingTypeLabel,
  formatFindingReason,
  formatMatchRate,
  parseFindingLocations,
} from "@/lib/scanReport";

export function FindingCard({ finding }: { finding: ScanFinding }) {
  const impact = findingImpact(finding.finding_type);
  const reason = finding.evidence?.reason ? String(finding.evidence.reason) : null;
  const locationInfo = parseFindingLocations(finding.evidence);

  return (
    <li className="rounded-lg border border-border bg-background-tertiary/50 p-4 transition-colors hover:border-border hover:bg-surface">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-semibold text-text-primary">{findingTypeLabel(finding.finding_type)}</p>
          {finding.column_name && (
            <p className="mt-1 text-sm text-text-muted">
              Affected column: <span className="font-mono text-text-secondary">{finding.column_name}</span>
            </p>
          )}
        </div>
        <SeverityBadge severity={finding.severity} />
      </div>

      {reason && (
        <p className="mt-2 text-sm text-text-secondary">{formatFindingReason(reason)}</p>
      )}

      {locationInfo && (
        <div className="mt-3 rounded-md border border-border/70 bg-background-secondary/40 px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Detected at ({locationInfo.label.toLowerCase()})
          </p>
          <ul className="mt-2 space-y-1.5">
            {locationInfo.locations.map((loc) => (
              <li key={loc.index} className="flex flex-wrap items-baseline gap-x-2 text-sm">
                <span className="font-mono font-medium text-text-primary">
                  {locationInfo.label} {loc.index}
                </span>
                {loc.preview && (
                  <span className="font-mono text-xs text-text-muted">→ {loc.preview}</span>
                )}
              </li>
            ))}
          </ul>
          {locationInfo.additionalCount > 0 && (
            <p className="mt-2 text-xs text-text-muted">
              +{locationInfo.additionalCount} more match{locationInfo.additionalCount === 1 ? "" : "es"} in scanned sample
            </p>
          )}
        </div>
      )}

      {impact && <p className="mt-2 text-xs leading-relaxed text-text-muted">{impact}</p>}

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-muted">
        <span>{finding.sample_count} matching row{finding.sample_count === 1 ? "" : "s"}</span>
        {finding.match_rate != null && <span>{formatMatchRate(finding.match_rate)}</span>}
      </div>
    </li>
  );
}

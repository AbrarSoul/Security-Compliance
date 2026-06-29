import type { ScanFinding } from "@/lib/types";
import { Badge, SeverityBadge } from "@/components/ui/Badge";
import {
  findingImpact,
  findingTypeLabel,
  formatComplianceGapExplanation,
  formatFindingReason,
  formatMatchRate,
  gapPriorityLabel,
  isComplianceGapFinding,
  isRuleBasedFinding,
  parseFindingLocations,
} from "@/lib/scanReport";

function gapTitle(finding: ScanFinding): string {
  const ruleName = finding.evidence?.rule_name;
  if (typeof ruleName === "string" && ruleName.trim()) {
    return ruleName;
  }
  return findingTypeLabel(finding.finding_type);
}

export function FindingCard({ finding }: { finding: ScanFinding }) {
  const isGap = isComplianceGapFinding(finding);
  const isRule = isRuleBasedFinding(finding);
  const impact = isGap ? null : findingImpact(finding.finding_type);
  const displayTitle =
    (finding.evidence?.rule_name != null && String(finding.evidence.rule_name).trim())
      ? String(finding.evidence.rule_name)
      : findingTypeLabel(finding.finding_type);
  const reason = finding.evidence?.reason ? String(finding.evidence.reason) : null;
  const explanation = isGap
    ? formatComplianceGapExplanation(finding)
    : finding.evidence?.explanation != null
      ? String(finding.evidence.explanation)
      : null;
  const ruleMessage = finding.evidence?.message != null ? String(finding.evidence.message) : null;
  const locationInfo = isGap ? null : parseFindingLocations(finding.evidence);
  const showRowStats = !isGap && finding.sample_count > 0;

  return (
    <li className="rounded-lg border border-border bg-background-tertiary/50 p-4 transition-colors hover:border-border hover:bg-surface">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-semibold text-text-primary">
            {isGap ? gapTitle(finding) : displayTitle}
          </p>
          {isGap && (
            <p className="mt-1 text-xs font-medium uppercase tracking-wide text-amber-600 dark:text-amber-400">
              Compliance gap
            </p>
          )}
          {finding.column_name && (
            <p className="mt-1 text-sm text-text-muted">
              Affected column: <span className="font-mono text-text-secondary">{finding.column_name}</span>
            </p>
          )}
        </div>
        {isGap ? (
          <Badge variant="warning">{gapPriorityLabel(finding.severity)}</Badge>
        ) : (
          <SeverityBadge severity={finding.severity} />
        )}
      </div>

      {isGap && (
        <p className="mt-2 text-sm text-text-secondary">
          This is not a detected threat — the file is missing content that your compliance rules
          expect (for example, policy language). <strong>High priority</strong> means the missing
          topic is important to address, not that harmful data was found.
        </p>
      )}

      {(explanation || ruleMessage) && (
        <p className="mt-2 text-sm text-text-secondary">{explanation ?? ruleMessage}</p>
      )}

      {reason && (
        <p className="mt-2 text-sm text-text-secondary">{formatFindingReason(reason)}</p>
      )}

      {locationInfo && (
        <div className="mt-3 rounded-md border border-border/70 bg-background-secondary/40 px-3 py-2.5">
          <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
            Found at ({locationInfo.label.toLowerCase()})
          </p>
          <ul className="mt-2 space-y-1.5">
            {locationInfo.locations.map((loc) => (
              <li key={`${loc.index}-${loc.preview ?? ""}`} className="flex flex-wrap items-baseline gap-x-2 text-sm">
                <span className="font-mono font-medium text-text-primary">
                  {locationInfo.label} {loc.index}
                  {finding.column_name ? ` · column '${finding.column_name}'` : ""}
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

      {showRowStats && (
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-muted">
          <span>
            {finding.sample_count} matching row{finding.sample_count === 1 ? "" : "s"}
          </span>
          {finding.match_rate != null && <span>{formatMatchRate(finding.match_rate)}</span>}
        </div>
      )}

      {isRule && finding.sample_count > 0 && !locationInfo && (
        <div className="mt-3 text-xs text-text-muted">
          Rule-based detection ({finding.sample_count} occurrence{finding.sample_count === 1 ? "" : "s"})
          {finding.evidence?.explanation ? ` — ${String(finding.evidence.explanation)}` : ""}
        </div>
      )}
    </li>
  );
}

import type { ComplianceScore } from "@/lib/types";
import { findingTypeLabel, riskBandLabel } from "@/lib/scanReport";
import { riskColor } from "@/lib/utils";

export function ScanScoreBreakdown({
  score,
  riskScore,
}: {
  score: ComplianceScore | null | undefined;
  riskScore: number | null | undefined;
}) {
  if (!score?.contributions?.length) return null;

  const sorted = [...score.contributions].sort((a, b) => b.total_points - a.total_points);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm text-text-muted">
          How the risk score was calculated from detected patterns in the sampled rows.
        </p>
        <p className={`text-sm font-semibold ${riskColor(riskScore)}`}>
          {riskBandLabel(riskScore)}
        </p>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border">
        <table className="w-full min-w-[480px] text-left text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-elevated text-xs uppercase tracking-wide text-text-muted">
              <th className="px-4 py-2.5 font-medium">Finding</th>
              <th className="px-4 py-2.5 font-medium">Column</th>
              <th className="px-4 py-2.5 font-medium">Severity</th>
              <th className="px-4 py-2.5 font-medium text-right">Points</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, i) => (
              <tr key={`${row.finding_type}-${row.column_name ?? i}`} className="border-b border-border/60 last:border-0">
                <td className="px-4 py-2.5 text-text-primary">{findingTypeLabel(row.finding_type)}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-text-muted">{row.column_name ?? "—"}</td>
                <td className="px-4 py-2.5 capitalize text-text-muted">{row.severity}</td>
                <td className="px-4 py-2.5 text-right font-mono text-text-primary">{row.total_points}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-surface-elevated/50">
              <td colSpan={3} className="px-4 py-2.5 text-xs font-medium uppercase tracking-wide text-text-muted">
                Total risk score
              </td>
              <td className={`px-4 py-2.5 text-right font-mono font-semibold ${riskColor(riskScore)}`}>
                {score.risk_score}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {score.adjustments && score.adjustments.length > 0 && (
        <ul className="space-y-1 text-xs text-text-muted">
          {score.adjustments.map((adj, i) => (
            <li key={i}>
              Status adjusted: {(adj as { reason?: string }).reason ?? "policy rule applied"}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

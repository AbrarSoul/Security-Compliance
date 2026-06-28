"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { FormField } from "@/components/forms/FormField";
import { Select } from "@/components/forms/Select";
import { StatCard } from "@/components/ui/StatCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { gapsApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { ComplianceGap, GapDashboard } from "@/lib/types/gaps";
import { FRAMEWORK_LABELS } from "@/lib/types/compliancePosture";
import { formatDate, severityVariant } from "@/lib/utils";

function severityBadge(severity: string) {
  return <Badge variant={severityVariant(severity)}>{severity}</Badge>;
}

function GapAnalysisContent() {
  const { hasPermission } = useAuth();
  const canAnalyze = hasPermission(PERMS.GAP_ANALYZE);
  const [dashboard, setDashboard] = useState<GapDashboard | null>(null);
  const [history, setHistory] = useState<ComplianceGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");
  const [frameworkFilter, setFrameworkFilter] = useState("");
  const [tab, setTab] = useState<"open" | "history">("open");

  const load = useCallback(async () => {
    setError(null);
    try {
      const dash = await gapsApi.dashboard();
      setDashboard(dash);
      if (tab === "history") {
        const hist = await gapsApi.history(
          severityFilter ? { severity: severityFilter } : undefined
        );
        setHistory(hist.items);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load gaps");
    } finally {
      setLoading(false);
    }
  }, [tab, severityFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAnalysis() {
    setAnalyzing(true);
    setError(null);
    try {
      await gapsApi.analyze();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleAcknowledge(gapId: string) {
    await gapsApi.acknowledge(gapId);
    await load();
  }

  async function handleResolve(gapId: string) {
    await gapsApi.resolve(gapId);
    await load();
  }

  const gaps = tab === "open" ? dashboard?.open_gaps ?? [] : history;
  const filteredGaps = gaps.filter((gap) => {
    if (!frameworkFilter) return true;
    return gap.framework_refs?.some((ref) => ref.framework === frameworkFilter);
  });

  const frameworkOptions = Object.entries(dashboard?.by_framework ?? {}).sort(
    ([, a], [, b]) => b - a
  );

  return (
    <>
      <Header
        title="Compliance gap analysis"
        subtitle="Identify missing protections and recommended remediations"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="flex flex-wrap gap-4">
            <FormField label="Severity filter">
              <Select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="">All</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </Select>
            </FormField>
            {tab === "open" && frameworkOptions.length > 0 && (
              <FormField label="Framework">
                <Select
                  value={frameworkFilter}
                  onChange={(e) => setFrameworkFilter(e.target.value)}
                >
                  <option value="">All frameworks</option>
                  {frameworkOptions.map(([id, count]) => (
                    <option key={id} value={id}>
                      {FRAMEWORK_LABELS[id] ?? id} ({count})
                    </option>
                  ))}
                </Select>
              </FormField>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant={tab === "open" ? "primary" : "secondary"}
              onClick={() => setTab("open")}
            >
              Open gaps
            </Button>
            <Button
              variant={tab === "history" ? "primary" : "secondary"}
              onClick={() => setTab("history")}
            >
              History
            </Button>
            {canAnalyze && (
              <Button onClick={() => void runAnalysis()} disabled={analyzing}>
                {analyzing ? "Analyzing…" : "Run analysis"}
              </Button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatCardSkeleton key={i} />
            ))}
          </div>
        ) : dashboard ? (
          <div className="animate-fade-in space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <StatCard
                label="Posture score"
                value={String(dashboard.posture_score)}
                subtext="100 = best"
              />
              <StatCard label="Open gaps" value={String(dashboard.open_total)} />
              <StatCard label="Critical" value={String(dashboard.by_severity.critical ?? 0)} />
              <StatCard label="High" value={String(dashboard.by_severity.high ?? 0)} />
              <StatCard
                label="Last analyzed"
                value={
                  dashboard.last_analyzed_at
                    ? formatDate(dashboard.last_analyzed_at)
                    : "Never"
                }
              />
            </div>

            {gaps.length === 0 ? (
              <Card className="p-8 text-center text-text-muted">
                {tab === "open"
                  ? "No open gaps. Run analysis to scan your compliance posture."
                  : "No historical gap records."}
              </Card>
            ) : filteredGaps.length === 0 ? (
              <Card className="p-8 text-center text-text-muted">
                No gaps match the selected framework filter.
              </Card>
            ) : (
              <div className="space-y-4">
                {filteredGaps.map((gap) => (
                  <Card key={gap.id} className="p-5">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold text-text-primary">{gap.title}</h3>
                          {severityBadge(gap.severity)}
                          <Badge variant="neutral">{gap.category}</Badge>
                          <Badge variant="neutral">{gap.gap_type.replace(/_/g, " ")}</Badge>
                        </div>
                        {(gap.framework_refs?.length ?? 0) > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {gap.framework_refs.map((ref) => (
                              <Badge key={`${ref.framework}-${ref.control_id}`} variant="neutral">
                                {FRAMEWORK_LABELS[ref.framework] ?? ref.framework}: {ref.control_id}
                              </Badge>
                            ))}
                          </div>
                        )}
                        <p className="mt-2 text-sm text-text-muted">{gap.description}</p>
                        <p className="mt-3 rounded-lg border border-border-accent bg-primary/10 px-3 py-2 text-sm text-text-secondary">
                          <span className="font-semibold text-primary">Remediation: </span>
                          {gap.recommendation}
                        </p>
                        <p className="mt-2 text-xs text-text-muted">
                          Score {gap.score} · Detected {formatDate(gap.detected_at)}
                        </p>
                      </div>
                      {canAnalyze && gap.status === "open" && tab === "open" && (
                        <div className="flex shrink-0 gap-2">
                          <Button
                            variant="secondary"
                            onClick={() => void handleAcknowledge(gap.id)}
                          >
                            Acknowledge
                          </Button>
                          <Button onClick={() => void handleResolve(gap.id)}>Resolve</Button>
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        ) : null}
      </div>
    </>
  );
}

export default function GapsPage() {
  return (
    <RequirePermission anyOf={[PERMS.GAP_READ, PERMS.GAP_READ_ALL]}>
      <GapAnalysisContent />
    </RequirePermission>
  );
}

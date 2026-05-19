"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { AnalyticsFiltersBar } from "@/components/analytics/AnalyticsFilters";
import { BarChartCard } from "@/components/analytics/charts/BarChartCard";
import { CountLineChartCard, LineChartCard } from "@/components/analytics/charts/LineChartCard";
import { PieChartCard } from "@/components/analytics/charts/PieChartCard";
import { HighRiskModelsTable, HighRiskUsersTable } from "@/components/analytics/HighRiskTable";
import { RealtimeViolationsWidget } from "@/components/analytics/RealtimeViolationsWidget";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { StatCard, StatCardWithRisk } from "@/components/ui/StatCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { analyticsApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { AnalyticsDashboard, AnalyticsFilters } from "@/lib/types/analytics";

const POLL_MS = 30_000;

const DEFAULT_FILTERS: AnalyticsFilters = {
  days: 30,
  severity: "",
  granularity: "day",
};

function AnalyticsDashboardContent() {
  const { hasPermission, isAuditor, isAdmin } = useAuth();
  const [filters, setFilters] = useState<AnalyticsFilters>(DEFAULT_FILTERS);
  const [data, setData] = useState<AnalyticsDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canViewOrg = hasPermission(PERMS.ANALYTICS_READ_ALL);

  const load = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      else setRefreshing(true);
      setError(null);
      try {
        const dash = await analyticsApi.dashboard({
          days: filters.days,
          severity: filters.severity || undefined,
          granularity: filters.granularity,
        });
        setData(dash);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load analytics");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [filters]
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const id = setInterval(() => void load(true), POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  const summary = data?.summary;

  return (
    <>
      <Header
        title="Analytics & monitoring"
        subtitle="Compliance trends, violations, and risk across your organization"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <AnalyticsFiltersBar filters={filters} onChange={setFilters} />

        {loading && !data ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <StatCardSkeleton key={i} />
            ))}
          </div>
        ) : data && summary ? (
          <div className="animate-fade-in space-y-6">
            <div className="flex flex-wrap items-center gap-2 text-xs text-text-muted">
              <span>
                Scope:{" "}
                <strong className="text-text-secondary">
                  {summary.scope === "organization" ? "Organization-wide" : "Your activity"}
                </strong>
              </span>
              {canViewOrg && (
                <Badge variant="info">{isAdmin ? "Admin" : isAuditor ? "Auditor" : "Org"}</Badge>
              )}
              {refreshing && <span className="text-text-accent">Refreshing…</span>}
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Violation events" value={String(summary.violation_events)} delay={0} />
              <StatCard label="Blocked executions" value={String(summary.blocked_executions)} delay={50} />
              <StatCard label="Policy violations" value={String(summary.policy_violations)} delay={100} />
              <StatCard label="Prompts blocked" value={String(summary.prompt_blocked)} delay={150} />
              <StatCard label="Outputs blocked" value={String(summary.output_blocked)} delay={200} />
              <StatCardWithRisk
                label="Avg prompt risk"
                value={summary.avg_prompt_risk != null ? String(Math.round(summary.avg_prompt_risk)) : "—"}
                score={summary.avg_prompt_risk}
                delay={250}
              />
              <StatCardWithRisk
                label="Avg output risk"
                value={summary.avg_output_risk != null ? String(Math.round(summary.avg_output_risk)) : "—"}
                score={summary.avg_output_risk}
                delay={300}
              />
              <StatCard
                label="Unread alerts"
                value={String(summary.unread_notifications)}
                delay={350}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              <div className="lg:col-span-2">
                <RealtimeViolationsWidget
                  items={data.realtime_violations}
                  refreshing={refreshing}
                />
              </div>
              <PieChartCard
                title="Prompt decisions"
                subtitle="Allow / warn / block"
                data={data.prompt_stats.decision_breakdown}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <CountLineChartCard
                title="Execution trends"
                subtitle="Executions over time"
                data={data.execution_trend}
              />
              <LineChartCard
                title="Risk trends"
                subtitle="Average scan risk score"
                data={data.risk_trend.map((p) => ({ bucket: p.bucket, value: p.value }))}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <CountLineChartCard
                title="Violation trends"
                subtitle="Compliance violations over time"
                data={data.violation_trend}
              />
              <CountLineChartCard
                title="Policy violation trends"
                subtitle="Policy events over time"
                data={data.policy_violation_trend}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <BarChartCard
                title="Blocked executions"
                subtitle="By status"
                data={data.blocked_executions.status_breakdown}
              />
              <PieChartCard
                title="Output leakage"
                subtitle="Blocked vs warned outputs"
                data={data.output_stats.leakage_breakdown}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <BarChartCard
                title="Guard enforcement"
                subtitle="Actions taken"
                data={data.guard_actions}
              />
              <CountLineChartCard
                title="Blocked execution trend"
                subtitle="Executions in range"
                data={data.blocked_executions.trend}
              />
            </div>

            {canViewOrg && (
              <div className="grid gap-6 lg:grid-cols-2">
                <HighRiskUsersTable items={data.high_risk_users} />
                <HighRiskModelsTable items={data.high_risk_models} />
              </div>
            )}
          </div>
        ) : null}
      </div>
    </>
  );
}

export default function AnalyticsPage() {
  return (
    <RequirePermission anyOf={[PERMS.ANALYTICS_READ, PERMS.ANALYTICS_READ_ALL]}>
      <AnalyticsDashboardContent />
    </RequirePermission>
  );
}

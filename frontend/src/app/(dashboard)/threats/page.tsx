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
import { threatsApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { SecurityEventLog, SecurityThreat, ThreatDashboard, UserBehaviorItem } from "@/lib/types/threats";
import { formatDate, severityVariant } from "@/lib/utils";

function ThreatMonitoringContent() {
  const { hasPermission, hasAnyPermission } = useAuth();
  const canManage = hasPermission(PERMS.THREAT_MANAGE);
  const canViewOrg = hasAnyPermission(PERMS.THREAT_READ_ALL);

  const [dashboard, setDashboard] = useState<ThreatDashboard | null>(null);
  const [events, setEvents] = useState<SecurityEventLog[]>([]);
  const [behavior, setBehavior] = useState<UserBehaviorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const [dash, ev, beh] = await Promise.all([
        threatsApi.dashboard(),
        threatsApi.events(),
        canViewOrg ? threatsApi.behavior() : Promise.resolve({ items: [] }),
      ]);
      setDashboard(dash);
      setEvents(ev.items);
      setBehavior(beh.items);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load threats");
    } finally {
      setLoading(false);
    }
  }, [canViewOrg]);

  useEffect(() => {
    void load();
    const id = setInterval(() => void load(), 30_000);
    return () => clearInterval(id);
  }, [load]);

  async function runDetection() {
    setDetecting(true);
    try {
      await threatsApi.detect();
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Detection failed");
    } finally {
      setDetecting(false);
    }
  }

  const threats = (dashboard?.open_threats ?? []).filter(
    (t) => !severityFilter || t.severity === severityFilter
  );

  return (
    <>
      <Header
        title="Security monitoring"
        subtitle="Threat detection, suspicious activity, and user behavior analysis"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap items-end justify-between gap-4">
          <FormField label="Severity">
            <Select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
              <option value="">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </Select>
          </FormField>
          {canManage && (
            <Button onClick={() => void runDetection()} disabled={detecting}>
              {detecting ? "Scanning…" : "Run threat detection"}
            </Button>
          )}
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
              <StatCard label="Security posture" value={String(dashboard.security_posture)} subtext="/ 100" />
              <StatCard label="Open threats" value={String(dashboard.open_total)} />
              <StatCard label="Critical" value={String(dashboard.by_severity.critical ?? 0)} />
              <StatCard label="High" value={String(dashboard.by_severity.high ?? 0)} />
              <StatCard
                label="Last scan"
                value={
                  dashboard.latest_run?.completed_at
                    ? formatDate(dashboard.latest_run.completed_at)
                    : "—"
                }
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-3">
              <div className="space-y-4 lg:col-span-2">
                <h2 className="text-sm font-semibold text-text-primary">Active threats</h2>
                {threats.length === 0 ? (
                  <Card className="p-8 text-center text-text-muted">No open threats in scope.</Card>
                ) : (
                  threats.map((t) => (
                    <ThreatCard
                      key={t.id}
                      threat={t}
                      canManage={canManage}
                      onUpdate={() => void load()}
                    />
                  ))
                )}
              </div>
              <div className="space-y-4">
                {canViewOrg && behavior.length > 0 && (
                  <Card className="p-5">
                    <h3 className="text-sm font-semibold text-text-primary">High-risk users</h3>
                    <ul className="mt-3 space-y-2 text-sm">
                      {behavior.map((b) => (
                        <li key={b.user_id} className="flex justify-between border-b border-border py-2">
                          <span className="truncate font-mono text-xs text-text-muted">{b.user_id.slice(0, 8)}…</span>
                          <Badge variant={severityVariant(b.risk_level)}>{b.risk_level}</Badge>
                        </li>
                      ))}
                    </ul>
                  </Card>
                )}
                <Card className="p-5">
                  <h3 className="text-sm font-semibold text-text-primary">Security event log</h3>
                  <ul className="mt-3 max-h-64 space-y-2 overflow-y-auto text-xs">
                    {events.length === 0 ? (
                      <li className="text-text-muted">No events yet</li>
                    ) : (
                      events.map((e) => (
                        <li key={e.id} className="rounded border border-border px-2 py-1.5">
                          <p className="font-medium text-text-secondary">{e.message}</p>
                          <p className="text-text-muted">{formatDate(e.created_at)}</p>
                        </li>
                      ))
                    )}
                  </ul>
                </Card>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </>
  );
}

function ThreatCard({
  threat,
  canManage,
  onUpdate,
}: {
  threat: SecurityThreat;
  canManage: boolean;
  onUpdate: () => void;
}) {
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-text-primary">{threat.title}</h3>
            <Badge variant={severityVariant(threat.severity)}>{threat.severity}</Badge>
            <Badge variant="neutral">{`Score ${threat.threat_score}`}</Badge>
          </div>
          <p className="mt-1 text-sm text-text-muted">{threat.description}</p>
          <p className="mt-1 text-xs text-text-muted">
            {threat.threat_type.replace(/_/g, " ")} · {formatDate(threat.detected_at)}
          </p>
        </div>
        {canManage && threat.status === "open" && (
          <div className="flex gap-2">
            <Button
              variant="secondary"
              onClick={() => threatsApi.investigate(threat.id).then(onUpdate)}
            >
              Investigate
            </Button>
            <Button onClick={() => threatsApi.resolve(threat.id).then(onUpdate)}>Resolve</Button>
          </div>
        )}
      </div>
    </Card>
  );
}

export default function ThreatsPage() {
  return (
    <RequirePermission anyOf={[PERMS.THREAT_READ, PERMS.THREAT_READ_ALL]}>
      <ThreatMonitoringContent />
    </RequirePermission>
  );
}

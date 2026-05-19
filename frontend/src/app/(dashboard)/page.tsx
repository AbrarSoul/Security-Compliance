"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { ComplianceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { IconChevronRight, IconFiles, IconReports, IconScan, IconShield } from "@/components/ui/icons";
import { StatCard, StatCardWithRisk } from "@/components/ui/StatCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import {
  executionsApi,
  filesApi,
  modelsApi,
  policiesApi,
  reportsApi,
  rulesApi,
  scansApi,
} from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { Report, Scan, UploadedFile } from "@/lib/types";
import { formatDate, riskColor } from "@/lib/utils";

export default function OverviewPage() {
  const { hasPermission, hasAnyPermission } = useAuth();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [policyCount, setPolicyCount] = useState<number | null>(null);
  const [ruleCount, setRuleCount] = useState<number | null>(null);
  const [executionCount, setExecutionCount] = useState<number | null>(null);
  const [modelCount, setModelCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tasks: Promise<void>[] = [
      filesApi.list().then((f) => setFiles(f.items)),
      scansApi.list().then((s) => setScans(s.items)),
      reportsApi.list().then((r) => setReports(r.items)),
    ];
    if (hasAnyPermission(PERMS.SCAN_READ, PERMS.POLICY_MANAGE)) {
      tasks.push(policiesApi.list({ limit: 1 }).then((p) => setPolicyCount(p.total)));
    }
    if (hasAnyPermission(PERMS.SCAN_READ, PERMS.RULE_MANAGE)) {
      tasks.push(rulesApi.list({ limit: 1 }).then((r) => setRuleCount(r.total)));
    }
    if (
      hasAnyPermission(
        PERMS.EXECUTION_REQUEST,
        PERMS.EXECUTION_READ,
        PERMS.EXECUTION_READ_ALL
      )
    ) {
      tasks.push(executionsApi.list({ limit: 1 }).then((e) => setExecutionCount(e.total)));
    }
    if (hasPermission(PERMS.SCAN_READ)) {
      tasks.push(modelsApi.list({ limit: 1 }).then((m) => setModelCount(m.total)));
    }
  void Promise.all(tasks).finally(() => setLoading(false));
  }, [hasPermission, hasAnyPermission]);

  const completedScans = scans.filter((s) => s.status === "completed");
  const avgRisk =
    completedScans.length > 0
      ? Math.round(
          completedScans.reduce((a, s) => a + (s.risk_score ?? 0), 0) / completedScans.length
        )
      : null;

  const statusCounts = {
    compliant: completedScans.filter((s) => s.compliance_status === "compliant").length,
    risky: completedScans.filter((s) => s.compliance_status === "risky").length,
    non_compliant: completedScans.filter((s) => s.compliance_status === "non_compliant").length,
  };
  const totalStatus = Math.max(
    statusCounts.compliant + statusCounts.risky + statusCounts.non_compliant,
    1
  );

  return (
    <>
      <Header
        title="Overview"
        subtitle="Monitor compliance posture across your datasets"
      />
      <div className="page-container">
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatCardSkeleton key={i} />
            ))}
          </div>
        ) : (
          <div className="animate-fade-in space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                label="Uploaded files"
                value={String(files.length)}
                delay={0}
                icon={<IconFiles className="h-5 w-5" />}
              />
              <StatCard
                label="Total scans"
                value={String(scans.length)}
                delay={50}
                icon={<IconScan className="h-5 w-5" />}
              />
              <StatCardWithRisk
                label="Avg risk score"
                value={avgRisk != null ? String(avgRisk) : "—"}
                score={avgRisk}
                delay={100}
              />
              <StatCard
                label="Reports"
                value={String(reports.length)}
                delay={150}
                icon={<IconReports className="h-5 w-5" />}
              />
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <Card title="Compliance breakdown">
                <div className="space-y-5">
                  <StatusRow
                    label="Compliant"
                    count={statusCounts.compliant}
                    total={totalStatus}
                    color="bg-flag-success"
                  />
                  <StatusRow
                    label="Risky"
                    count={statusCounts.risky}
                    total={totalStatus}
                    color="bg-flag-warning"
                  />
                  <StatusRow
                    label="Non-compliant"
                    count={statusCounts.non_compliant}
                    total={totalStatus}
                    color="bg-flag-danger"
                  />
                </div>
              </Card>

              <Card
                title="Recent scans"
                action={
                  <Link href="/scans">
                    <Button variant="ghost" className="gap-1 text-text-accent">
                      View all <IconChevronRight />
                    </Button>
                  </Link>
                }
              >
                {scans.length === 0 ? (
                  <p className="text-sm text-text-muted">
                    No scans yet. Upload a file and run a scan to get started.
                  </p>
                ) : (
                  <ul className="divide-y divide-border">
                    {scans.slice(0, 5).map((scan) => (
                      <li
                        key={scan.id}
                        className="-mx-2 flex items-center justify-between rounded-lg px-2 py-3 transition-colors first:pt-0 last:pb-0 hover:bg-background-tertiary/50"
                      >
                        <div>
                          <Link
                            href={`/scans/${scan.id}`}
                            className="text-sm font-semibold text-text-primary transition-colors hover:text-text-accent"
                          >
                            Scan {scan.id.slice(0, 8)}…
                          </Link>
                          <p className="text-xs text-text-muted">{formatDate(scan.created_at)}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`font-mono text-sm font-bold ${riskColor(scan.risk_score)}`}>
                            {scan.risk_score ?? "—"}
                          </span>
                          <ComplianceBadge status={scan.compliance_status} />
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </Card>
            </div>

            {(policyCount != null ||
              ruleCount != null ||
              executionCount != null ||
              modelCount != null) && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {policyCount != null && (
                  <StatCard
                    label="Policies"
                    value={String(policyCount)}
                    icon={<IconShield className="h-5 w-5" />}
                  />
                )}
                {ruleCount != null && (
                  <StatCard
                    label="Rules"
                    value={String(ruleCount)}
                    icon={<IconShield className="h-5 w-5" />}
                  />
                )}
                {executionCount != null && (
                  <StatCard
                    label="Executions"
                    value={String(executionCount)}
                    icon={<IconShield className="h-5 w-5" />}
                  />
                )}
                {modelCount != null && (
                  <StatCard
                    label="Models"
                    value={String(modelCount)}
                    icon={<IconShield className="h-5 w-5" />}
                  />
                )}
              </div>
            )}

            <Card title="Quick actions">
              <div className="flex flex-wrap gap-3">
                <Link href="/files">
                  <Button>Upload dataset</Button>
                </Link>
                <Link href="/scans">
                  <Button variant="secondary">View scans</Button>
                </Link>
                <Link href="/reports">
                  <Button variant="outline">View reports</Button>
                </Link>
                {hasAnyPermission(
                  PERMS.EXECUTION_REQUEST,
                  PERMS.EXECUTION_READ,
                  PERMS.EXECUTION_READ_ALL
                ) && (
                  <Link href="/executions">
                    <Button variant="outline">Executions</Button>
                  </Link>
                )}
                {hasPermission(PERMS.EXECUTION_REQUEST) && (
                  <Link href="/executions/validate">
                    <Button variant="outline">Validate execution</Button>
                  </Link>
                )}
                {hasAnyPermission(PERMS.SCAN_READ, PERMS.POLICY_MANAGE) && (
                  <Link href="/policies">
                    <Button variant="ghost">Policies</Button>
                  </Link>
                )}
                {hasAnyPermission(PERMS.SCAN_READ, PERMS.RULE_MANAGE) && (
                  <Link href="/rules">
                    <Button variant="ghost">Rules</Button>
                  </Link>
                )}
                {hasPermission(PERMS.SCAN_READ) && (
                  <Link href="/models">
                    <Button variant="ghost">Models</Button>
                  </Link>
                )}
                {hasPermission(PERMS.AUDIT_READ) && (
                  <Link href="/audit">
                    <Button variant="ghost">Audit logs</Button>
                  </Link>
                )}
              </div>
            </Card>
          </div>
        )}
      </div>
    </>
  );
}

function StatusRow({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: string;
}) {
  const pct = Math.round((count / total) * 100);
  return (
    <div>
      <div className="mb-2 flex justify-between text-sm">
        <span className="font-medium text-text-secondary">{label}</span>
        <span className="font-mono text-text-muted">
          {count} <span className="text-text-muted">({pct}%)</span>
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-surface-elevated">
        <div
          className={`h-full rounded-full ${color} transition-all duration-700 ease-out`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

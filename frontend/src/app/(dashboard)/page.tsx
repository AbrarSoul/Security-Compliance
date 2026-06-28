"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Badge, ComplianceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { IconChevronRight, IconFiles, IconReports, IconScan, IconShield } from "@/components/ui/icons";
import { StatCard, StatCardWithRisk } from "@/components/ui/StatCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import {
  compliancePostureApi,
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
import type { FrameworkPosture } from "@/lib/types/compliancePosture";
import {
  POSTURE_STATUS_LABELS,
  postureStatusVariant,
} from "@/lib/types/compliancePosture";
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
  const [frameworkPosture, setFrameworkPosture] = useState<FrameworkPosture[] | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tasks: Promise<void>[] = [];

    if (hasPermission(PERMS.FILE_READ)) {
      tasks.push(
        filesApi
          .list()
          .then((f) => setFiles(f.items))
          .catch(() => setFiles([]))
      );
    }
    if (hasPermission(PERMS.SCAN_READ)) {
      tasks.push(
        scansApi
          .list()
          .then((s) => setScans(s.items))
          .catch(() => setScans([]))
      );
    }
    if (hasAnyPermission(PERMS.REPORT_READ, PERMS.REPORT_READ_ALL)) {
      tasks.push(
        reportsApi
          .list()
          .then((r) => setReports(r.items))
          .catch(() => setReports([]))
      );
    }
    if (hasAnyPermission(PERMS.SCAN_READ, PERMS.POLICY_MANAGE)) {
      tasks.push(
        policiesApi
          .list({ limit: 1 })
          .then((p) => setPolicyCount(p.total))
          .catch(() => setPolicyCount(null))
      );
    }
    if (hasAnyPermission(PERMS.SCAN_READ, PERMS.RULE_MANAGE)) {
      tasks.push(
        rulesApi
          .list({ limit: 1 })
          .then((r) => setRuleCount(r.total))
          .catch(() => setRuleCount(null))
      );
    }
    if (
      hasAnyPermission(
        PERMS.EXECUTION_REQUEST,
        PERMS.EXECUTION_READ,
        PERMS.EXECUTION_READ_ALL
      )
    ) {
      tasks.push(
        executionsApi
          .list({ limit: 1 })
          .then((e) => setExecutionCount(e.total))
          .catch(() => setExecutionCount(null))
      );
    }
    if (hasPermission(PERMS.SCAN_READ)) {
      tasks.push(
        modelsApi
          .list({ limit: 1 })
          .then((m) => setModelCount(m.total))
          .catch(() => setModelCount(null))
      );
    }
    if (
      hasAnyPermission(PERMS.GAP_READ, PERMS.GAP_READ_ALL, PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL)
    ) {
      tasks.push(
        compliancePostureApi
          .get()
          .then((p) => setFrameworkPosture(p.frameworks))
          .catch(() => setFrameworkPosture(null))
      );
    }

    if (tasks.length === 0) {
      setLoading(false);
      return;
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

            {frameworkPosture && frameworkPosture.length > 0 && (
              <Card
                title="Framework compliance"
                action={
                  <Link href="/compliance">
                    <Button variant="ghost" className="gap-1 text-text-accent">
                      Full posture <IconChevronRight />
                    </Button>
                  </Link>
                }
              >
                <div className="grid gap-3 sm:grid-cols-3">
                  {frameworkPosture.map((fw) => (
                    <div
                      key={fw.id}
                      className="rounded-lg border border-border bg-background-secondary/40 p-4"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-sm font-semibold text-text-primary">{fw.name}</p>
                        <Badge variant={postureStatusVariant(fw.status)}>
                          {POSTURE_STATUS_LABELS[fw.status] ?? fw.status}
                        </Badge>
                      </div>
                      <p className="mt-2 text-xs text-text-muted">
                        {fw.open_issue_count} open issue{fw.open_issue_count === 1 ? "" : "s"}
                        {fw.alignment_score != null && ` · ${fw.alignment_score}% alignment`}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

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
                {hasPermission(PERMS.FILE_READ) && (
                  <Link href="/files">
                    <Button>Upload dataset</Button>
                  </Link>
                )}
                {hasPermission(PERMS.SCAN_READ) && (
                  <Link href="/scans">
                    <Button variant="secondary">View scans</Button>
                  </Link>
                )}
                {hasAnyPermission(PERMS.REPORT_READ, PERMS.REPORT_READ_ALL) && (
                  <Link href="/reports">
                    <Button variant="outline">View reports</Button>
                  </Link>
                )}
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

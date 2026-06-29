"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { compliancePostureApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { CompliancePosture, FrameworkPosture } from "@/lib/types/compliancePosture";
import {
  FRAMEWORK_LABELS,
  POSTURE_STATUS_LABELS,
  postureStatusVariant,
} from "@/lib/types/compliancePosture";
import { formatDate, severityVariant } from "@/lib/utils";

function statusBadge(status: string) {
  return (
    <Badge variant={postureStatusVariant(status)}>
      {POSTURE_STATUS_LABELS[status] ?? status}
    </Badge>
  );
}

function FrameworkCard({ framework }: { framework: FrameworkPosture }) {
  const [expanded, setExpanded] = useState(framework.open_issue_count > 0);

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-text-primary">{framework.name}</h3>
            {statusBadge(framework.status)}
          </div>
          <p className="mt-1 text-sm text-text-muted">{framework.description}</p>
          <div className="mt-3 flex flex-wrap gap-4 text-sm text-text-secondary">
            {framework.alignment_score != null && (
              <span>
                Alignment:{" "}
                <span className="font-mono font-semibold">{framework.alignment_score}%</span>
              </span>
            )}
            {framework.id === "nist_ai_rmf" && framework.summary?.violations != null && (
              <span>
                Violations:{" "}
                <span className="font-mono font-semibold">{framework.summary.violations}</span>
              </span>
            )}
            {framework.id === "nist_ai_rmf" && framework.summary?.alignment_gaps != null && (
              <span>
                Setup gaps:{" "}
                <span className="font-mono font-semibold">{framework.summary.alignment_gaps}</span>
              </span>
            )}
            <span>
              Open issues:{" "}
              <span className="font-mono font-semibold">{framework.open_issue_count}</span>
            </span>
          </div>
        </div>
        <Link href={framework.detail_url}>
          <Button variant="secondary">View details</Button>
        </Link>
      </div>

      {framework.open_issues.length > 0 && (
        <div className="mt-4 border-t border-border pt-4">
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="text-sm font-medium text-primary hover:underline"
          >
            {expanded ? "Hide" : "Show"} issues to fix ({framework.open_issues.length})
          </button>
          {expanded && (
            <ul className="mt-3 space-y-3">
              {framework.open_issues.map((issue) => (
                <li
                  key={`${issue.source}-${issue.id}`}
                  className="rounded-lg border border-border bg-background-secondary/50 p-3"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">{issue.title}</span>
                    <Badge variant={severityVariant(issue.severity)}>{issue.severity}</Badge>
                    {issue.control_ids.slice(0, 3).map((cid) => (
                      <Badge key={cid} variant="neutral">
                        {cid}
                      </Badge>
                    ))}
                  </div>
                  <p className="mt-2 text-sm text-text-muted">
                    <span className="font-semibold text-primary">Fix: </span>
                    {issue.remediation}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {framework.open_issues.length === 0 && framework.status === "met" && (
        <p className="mt-4 text-sm text-text-muted">No open issues for this framework.</p>
      )}
    </Card>
  );
}

function CompliancePostureContent() {
  const [posture, setPosture] = useState<CompliancePosture | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await compliancePostureApi.get();
      setPosture(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load compliance posture");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const summary = useMemo(() => {
    if (!posture) return null;
    const met = posture.frameworks.filter((f) => f.status === "met").length;
    const partial = posture.frameworks.filter((f) => f.status === "partial").length;
    const notMet = posture.frameworks.filter((f) => f.status === "not_met").length;
    const totalIssues = posture.frameworks.reduce((a, f) => a + f.open_issue_count, 0);
    return { met, partial, notMet, totalIssues };
  }, [posture]);

  return (
    <>
      <Header
        title="Compliance posture"
        subtitle="Per-framework alignment — what you meet and what to fix"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}
        {posture && <Alert variant="info">{posture.disclaimer}</Alert>}

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatCardSkeleton key={i} />
            ))}
          </div>
        ) : posture && summary ? (
          <div className="animate-fade-in space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard label="Frameworks tracked" value={String(posture.frameworks.length)} />
              <StatCard label="Compliant" value={String(summary.met)} />
              <StatCard label="Partial" value={String(summary.partial)} />
              <StatCard label="Open issues" value={String(summary.totalIssues)} />
            </div>

            <p className="text-xs text-text-muted">
              Evaluated {formatDate(posture.evaluated_at)}
              {posture.last_gap_analysis_at &&
                ` · Last gap analysis ${formatDate(posture.last_gap_analysis_at)}`}
            </p>

            <div className="space-y-4">
              {posture.frameworks.map((framework) => (
                <FrameworkCard key={framework.id} framework={framework} />
              ))}
            </div>

            <Card className="p-4">
              <div className="flex flex-wrap gap-3">
                <Link href="/gaps">
                  <Button variant="secondary">Gap analysis</Button>
                </Link>
                <Link href="/nist-ai-rmf">
                  <Button variant="outline">NIST AI RMF profile</Button>
                </Link>
                <Link href="/gaira">
                  <Button variant="outline">GAIRA inventory</Button>
                </Link>
              </div>
            </Card>
          </div>
        ) : null}
      </div>
    </>
  );
}

export default function CompliancePosturePage() {
  return (
    <RequirePermission
      anyOf={[PERMS.GAP_READ, PERMS.GAP_READ_ALL, PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL]}
    >
      <CompliancePostureContent />
    </RequirePermission>
  );
}

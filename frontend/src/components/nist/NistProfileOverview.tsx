"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { CollapsibleSection } from "@/components/ui/CollapsibleSection";
import {
  buildProfileInsights,
  controlDisplayInfo,
  NIST_BAR_SEGMENT_INFO,
  NIST_FINDING_KIND_INFO,
  NIST_FUNCTION_INFO,
  NIST_STATUS_INFO,
  type NistActionItem,
} from "@/lib/nistAiRmfInsights";
import type { NistControlStatus, NistCurrentProfile } from "@/lib/types/nistAiRmf";
import { NIST_FUNCTIONS } from "@/lib/types/nistAiRmf";
import { formatDate } from "@/lib/utils";

function statusBadgeVariant(control: NistActionItem["control"]) {
  const info = controlDisplayInfo(control);
  return info.badgeVariant ?? "neutral";
}

function ActionItemRow({ item }: { item: NistActionItem }) {
  return (
    <li className="rounded-lg border border-border bg-background-secondary/40 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-primary">{item.control.id}</span>
            <Badge variant={item.priority === "high" ? "danger" : "warning"}>
              {item.priority === "high" ? "Violation" : "Setup gap"}
            </Badge>
            <Badge variant={statusBadgeVariant(item.control)}>
              {controlDisplayInfo(item.control).short}
            </Badge>
          </div>
          <p className="mt-2 text-sm text-text-primary">{item.control.text}</p>
          <p className="mt-2 text-sm text-text-muted">
            <span className="font-medium text-text-secondary">Why: </span>
            {item.reason}
          </p>
        </div>
        {item.action && (
          <Link href={item.action.href}>
            <Button variant="secondary">{item.action.label}</Button>
          </Link>
        )}
      </div>
    </li>
  );
}

export function NistProfileOverview({ profile }: { profile: NistCurrentProfile }) {
  const insights = buildProfileInsights(profile);

  return (
    <div className="space-y-6">
      <Card className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-text-muted">
              Alignment score
            </p>
            <h2 className="mt-1 font-mono text-4xl font-semibold text-text-primary">
              {profile.alignment_score}%
            </h2>
            <p className="mt-2 text-sm text-text-muted">{insights.complianceSummary}</p>
            <p className="mt-3 max-w-3xl text-xs text-text-muted">
              Violations are active policy breaches (e.g. unapproved models, apps without GAIRA);
              setup gaps are unmet requirements during onboarding and are not non-compliance.
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-text-muted">Status</p>
            <p className="mt-1 text-lg font-semibold text-text-primary">
              {insights.profileHeadline}
            </p>
            <p className="mt-2 text-xs text-text-muted">{insights.readinessSummary}</p>
          </div>
        </div>

        <div className="mt-5">
          <div
            className="flex h-3 w-full overflow-hidden rounded-full bg-background-tertiary"
            role="img"
            aria-label={`Readiness breakdown: ${insights.readinessSummary}`}
          >
            {insights.breakdown.map((segment) => (
              <div
                key={segment.key}
                className={`${NIST_BAR_SEGMENT_INFO[segment.key].color} transition-all`}
                style={{ width: `${segment.percent}%` }}
                title={`${NIST_BAR_SEGMENT_INFO[segment.key].label}: ${segment.count}`}
              />
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-xs text-text-muted">
            {insights.breakdown.map((segment) => (
              <span key={segment.key} className="inline-flex items-center gap-1.5">
                <span
                  className={`inline-block h-2.5 w-2.5 rounded-full ${NIST_BAR_SEGMENT_INFO[segment.key].color}`}
                />
                {NIST_BAR_SEGMENT_INFO[segment.key].label} ({segment.count})
              </span>
            ))}
          </div>
        </div>

        <p className="mt-4 text-sm text-text-muted">{insights.scoreExplanation}</p>
        <p className="mt-2 text-xs text-text-muted">
          {insights.automatedCount} of {profile.summary.total} requirements were automatically
          checked from platform data · Evaluated {formatDate(profile.evaluated_at)}
        </p>
      </Card>

      <Card className="p-5">
        <h3 className="text-sm font-semibold text-text-primary">What each label means</h3>
        <p className="mt-1 text-sm text-text-muted">
          Compliance status depends on <strong className="font-medium text-text-secondary">violations</strong> only.
          Setup gaps and &quot;not checked yet&quot; items do not make you non-compliant.
        </p>
        <dl className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {(["violation", "alignment_gap", "improvement"] as const).map((kind) => (
            <div
              key={kind}
              className="rounded-lg border border-border bg-background-secondary/30 px-3 py-3"
            >
              <dt className="flex items-center gap-2">
                <Badge variant={NIST_FINDING_KIND_INFO[kind].badgeVariant}>
                  {NIST_FINDING_KIND_INFO[kind].label}
                </Badge>
              </dt>
              <dd className="mt-2 text-xs text-text-muted">
                {NIST_FINDING_KIND_INFO[kind].description}
              </dd>
            </div>
          ))}
          {(Object.keys(NIST_STATUS_INFO) as NistControlStatus[])
            .filter((s) => s === "met" || s === "not_assessed" || s === "not_applicable")
            .map((status) => (
            <div
              key={status}
              className="rounded-lg border border-border bg-background-secondary/30 px-3 py-3"
            >
              <dt className="flex items-center gap-2">
                <Badge variant={status === "met" ? "success" : "neutral"}>
                  {NIST_STATUS_INFO[status].label}
                </Badge>
                <span className="text-xs text-text-muted">
                  {profile.summary[status]} of {profile.summary.total}
                </span>
              </dt>
              <dd className="mt-2 text-xs text-text-muted">{NIST_STATUS_INFO[status].description}</dd>
            </div>
          ))}
        </dl>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {NIST_FUNCTIONS.map((fn) => {
          const info = NIST_FUNCTION_INFO[fn];
          const s = profile.by_function[fn];
          if (!s || !info) return null;
          const checked = s.met + s.partial + s.not_met;
          return (
            <Card key={fn} className="p-4">
              <h3 className="text-sm font-semibold text-text-primary">{info.title}</h3>
              <p className="mt-1 text-xs text-text-muted">{info.description}</p>
              <dl className="mt-3 space-y-1 text-xs">
                <div className="flex justify-between text-text-muted">
                  <dt>Satisfied</dt>
                  <dd className="font-mono text-text-secondary">{s.met}</dd>
                </div>
                <div className="flex justify-between text-text-muted">
                  <dt>Partial</dt>
                  <dd className="font-mono text-text-secondary">{s.partial}</dd>
                </div>
                <div className="flex justify-between text-text-muted">
                  <dt>Violations</dt>
                  <dd className="font-mono text-text-secondary">{s.violations ?? 0}</dd>
                </div>
                <div className="flex justify-between text-text-muted">
                  <dt>Setup gaps</dt>
                  <dd className="font-mono text-text-secondary">{s.alignment_gaps ?? 0}</dd>
                </div>
                <div className="flex justify-between text-text-muted">
                  <dt>Auto-checked</dt>
                  <dd className="font-mono text-text-secondary">{checked}</dd>
                </div>
              </dl>
            </Card>
          );
        })}
      </div>

      <CollapsibleSection
        title="What to do next"
        subtitle="Violations first, then setup gaps."
        meta={
          insights.actionItems.length > 0
            ? `${insights.actionItems.length} item${insights.actionItems.length === 1 ? "" : "s"}`
            : undefined
        }
      >
        {insights.actionItems.length > 0 ? (
          <>
            <ul className="divide-y divide-border px-5 py-2">
              {insights.actionItems.slice(0, 8).map((item) => (
                <ActionItemRow key={item.control.id} item={item} />
              ))}
            </ul>
            {insights.actionItems.length > 8 && (
              <p className="border-t border-border px-5 py-3 text-xs text-text-muted">
                {insights.actionItems.length - 8} more items — use All requirements below with
                filters.
              </p>
            )}
          </>
        ) : (
          <p className="px-5 py-4 text-sm text-text-muted">
            No violations or setup gaps detected from automated checks.
          </p>
        )}
      </CollapsibleSection>
    </div>
  );
}

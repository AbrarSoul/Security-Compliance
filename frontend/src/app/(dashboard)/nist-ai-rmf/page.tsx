"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Header } from "@/components/layout/Header";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { FormField } from "@/components/forms/FormField";
import { Select } from "@/components/forms/Select";
import { StatCard } from "@/components/ui/StatCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { nistAiRmfApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { NistControlStatusItem, NistCurrentProfile } from "@/lib/types/nistAiRmf";
import { NIST_FUNCTIONS, NIST_STATUS_LABELS } from "@/lib/types/nistAiRmf";
import { formatDate } from "@/lib/utils";

function statusBadge(status: string) {
  const key = status as keyof typeof NIST_STATUS_LABELS;
  const variant =
    status === "met"
      ? "success"
      : status === "partial"
        ? "warning"
        : status === "not_met"
          ? "danger"
          : "neutral";
  return (
    <Badge variant={variant}>
      {NIST_STATUS_LABELS[key] ?? status}
    </Badge>
  );
}

function NistAiRmfContent() {
  const [profile, setProfile] = useState<NistCurrentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [functionFilter, setFunctionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await nistAiRmfApi.currentProfile();
      setProfile(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load NIST AI RMF profile");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const controls = useMemo(() => {
    if (!profile) return [];
    return profile.controls.filter((c) => {
      if (functionFilter && c.function !== functionFilter) return false;
      if (statusFilter && c.status !== statusFilter) return false;
      return true;
    });
  }, [profile, functionFilter, statusFilter]);

  return (
    <>
      <Header
        title="NIST AI RMF"
        subtitle="Operational alignment with Govern · Map · Measure · Manage"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}
        {profile && (
          <Alert variant="info">{profile.disclaimer}</Alert>
        )}

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatCardSkeleton key={i} />
            ))}
          </div>
        ) : profile ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <StatCard
                label="Alignment score"
                value={`${profile.alignment_score}%`}
              />
              <StatCard label="Met" value={String(profile.summary.met)} />
              <StatCard label="Partial" value={String(profile.summary.partial)} />
              <StatCard label="Not met" value={String(profile.summary.not_met)} />
              <StatCard
                label="Evaluated at"
                value={formatDate(profile.evaluated_at)}
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {NIST_FUNCTIONS.map((fn) => {
                const s = profile.by_function[fn];
                if (!s) return null;
                return (
                  <Card key={fn} className="p-4">
                    <h3 className="text-sm font-semibold text-text-primary">{fn}</h3>
                    <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-text-muted">
                      <dt>Met</dt>
                      <dd className="text-text-secondary">{s.met}</dd>
                      <dt>Partial</dt>
                      <dd className="text-text-secondary">{s.partial}</dd>
                      <dt>Not met</dt>
                      <dd className="text-text-secondary">{s.not_met}</dd>
                      <dt>Not assessed</dt>
                      <dd className="text-text-secondary">{s.not_assessed}</dd>
                    </dl>
                  </Card>
                );
              })}
            </div>

            <div className="flex flex-wrap gap-4">
              <FormField label="Function">
                <Select
                  value={functionFilter}
                  onChange={(e) => setFunctionFilter(e.target.value)}
                >
                  <option value="">All functions</option>
                  {NIST_FUNCTIONS.map((fn) => (
                    <option key={fn} value={fn}>
                      {fn}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Status">
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <option value="">All statuses</option>
                  {Object.entries(NIST_STATUS_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              </FormField>
            </div>

            <Card className="overflow-hidden">
              <div className="border-b border-border px-4 py-3">
                <h2 className="text-sm font-semibold text-text-primary">
                  Controls ({controls.length} of {profile.summary.total})
                </h2>
                <p className="text-xs text-text-muted">
                  {profile.profile_name} · NIST AI RMF {profile.framework_version}
                </p>
              </div>
              <ul className="divide-y divide-border">
                {controls.map((control: NistControlStatusItem) => (
                  <li key={control.id} className="px-4 py-4">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="font-mono text-xs text-primary">{control.id}</p>
                        <p className="mt-1 text-sm text-text-primary">{control.text}</p>
                        {control.evidence.length > 0 && (
                          <ul className="mt-2 list-inside list-disc text-xs text-text-muted">
                            {control.evidence.map((line) => (
                              <li key={line}>{line}</li>
                            ))}
                          </ul>
                        )}
                        {control.notes && (
                          <p className="mt-2 text-xs text-text-muted">{control.notes}</p>
                        )}
                        {control.modules.length > 0 && (
                          <p className="mt-2 text-[10px] uppercase tracking-wide text-text-muted">
                            Modules: {control.modules.join(", ")}
                          </p>
                        )}
                      </div>
                      {statusBadge(control.status)}
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          </>
        ) : null}
      </div>
    </>
  );
}

export default function NistAiRmfPage() {
  return (
    <RequirePermission anyOf={[PERMS.GAP_READ, PERMS.GAP_READ_ALL, PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL]}>
      <NistAiRmfContent />
    </RequirePermission>
  );
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Header } from "@/components/layout/Header";
import { NistControlRow } from "@/components/nist/NistControlRow";
import { NistProfileOverview } from "@/components/nist/NistProfileOverview";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { Alert } from "@/components/ui/Alert";
import { CollapsibleSection } from "@/components/ui/CollapsibleSection";
import { FormField } from "@/components/forms/FormField";
import { Select } from "@/components/forms/Select";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { nistAiRmfApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import { NIST_FUNCTION_INFO } from "@/lib/nistAiRmfInsights";
import type { NistCurrentProfile, NistFindingKind } from "@/lib/types/nistAiRmf";
import { NIST_FINDING_KIND_LABELS, NIST_FUNCTIONS, NIST_STATUS_LABELS } from "@/lib/types/nistAiRmf";

function NistAiRmfContent() {
  const [profile, setProfile] = useState<NistCurrentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [functionFilter, setFunctionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [findingFilter, setFindingFilter] = useState("");

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
      if (findingFilter && c.finding_kind !== findingFilter) return false;
      return true;
    });
  }, [profile, functionFilter, statusFilter, findingFilter]);

  return (
    <>
      <Header
        title="NIST AI RMF"
        subtitle="How your organization's AI governance aligns with NIST — Govern · Map · Measure · Manage"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}
        {profile && (
          <Alert variant="info">
            {profile.disclaimer} Use the sections below to see what is satisfied, what needs work,
            and which items are not automatically checked.
          </Alert>
        )}

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <StatCardSkeleton key={i} />
            ))}
          </div>
        ) : profile ? (
          <>
            <NistProfileOverview profile={profile} />

            <CollapsibleSection
              title={`All requirements (${controls.length} of ${profile.summary.total})`}
              subtitle={`${profile.profile_name} · NIST AI RMF ${profile.framework_version}`}
              meta="72 controls"
            >
              <div className="flex flex-wrap gap-4 border-b border-border px-4 py-4">
                <FormField label="Area">
                  <Select
                    value={functionFilter}
                    onChange={(e) => setFunctionFilter(e.target.value)}
                  >
                    <option value="">All areas</option>
                    {NIST_FUNCTIONS.map((fn) => (
                      <option key={fn} value={fn}>
                        {NIST_FUNCTION_INFO[fn]?.title ?? fn}
                      </option>
                    ))}
                  </Select>
                </FormField>
                <FormField label="Finding type">
                  <Select
                    value={findingFilter}
                    onChange={(e) => setFindingFilter(e.target.value)}
                  >
                    <option value="">All finding types</option>
                    {(["violation", "alignment_gap", "improvement"] as NistFindingKind[]).map(
                      (kind) => (
                        <option key={kind} value={kind}>
                          {NIST_FINDING_KIND_LABELS[kind]}
                        </option>
                      )
                    )}
                  </Select>
                </FormField>
                <FormField label="Raw status">
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
              {controls.length === 0 ? (
                <p className="px-4 py-8 text-center text-sm text-text-muted">
                  No requirements match the selected filters.
                </p>
              ) : (
                <ul className="divide-y divide-border">
                  {controls.map((control) => (
                    <NistControlRow key={control.id} control={control} />
                  ))}
                </ul>
              )}
            </CollapsibleSection>
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

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { EmptyState } from "@/components/ui/EmptyState";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { FormField } from "@/components/forms/FormField";
import { Textarea } from "@/components/forms/Textarea";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { gairaApi, ApiError } from "@/lib/api";
import { notifyGairaRegistrationUpdated } from "@/hooks/usePendingGairaRegistrationCount";
import { PERMS } from "@/lib/permissions";
import type { AIApplication } from "@/lib/types/gaira";
import { formatDate } from "@/lib/utils";

export default function GairaApprovalsPage() {
  return (
    <RequirePermission permission={PERMS.GAIRA_APPROVE}>
      <ApprovalsContent />
    </RequirePermission>
  );
}

function ApprovalsContent() {
  const [pending, setPending] = useState<AIApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [rejectReasonByApp, setRejectReasonByApp] = useState<Record<string, string>>({});
  const [actingId, setActingId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    gairaApi
      .listPendingAdmin()
      .then((res) => setPending(res.items))
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => {
        setLoading(false);
        notifyGairaRegistrationUpdated();
      });
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function approve(applicationId: string) {
    setActingId(applicationId);
    setError("");
    setMessage("");
    try {
      const res = await gairaApi.approveApplication(applicationId);
      setMessage(res.message);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Approval failed");
    } finally {
      setActingId(null);
    }
  }

  async function reject(applicationId: string) {
    const reason = (rejectReasonByApp[applicationId] ?? "").trim();
    if (!reason) {
      setError("A rejection reason is required.");
      return;
    }
    if (!confirm("Reject this AI application registration?")) return;
    setActingId(applicationId);
    setError("");
    setMessage("");
    try {
      const res = await gairaApi.rejectApplication(applicationId, reason);
      setMessage(res.message);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Rejection failed");
    } finally {
      setActingId(null);
    }
  }

  return (
    <>
      <Header
        title="GAIRA registration approvals"
        subtitle="Approve or reject AI applications after auditor review"
      />
      <div className="page-container space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}

        <Card title="Awaiting admin decision">
          {loading ? (
            <TableSkeleton rows={4} />
          ) : pending.length === 0 ? (
            <EmptyState
              title="No pending approvals"
              description="Applications will appear here after an auditor submits feedback."
            />
          ) : (
            <div className="space-y-6">
              {pending.map((app) => (
                <div
                  key={app.id}
                  className="rounded-lg border border-border bg-background-tertiary/30 p-4"
                >
                  <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h3 className="font-medium text-text-primary">{app.name}</h3>
                      <p className="text-sm text-text-muted">
                        Owner: {app.owner_name ?? "—"} · Reviewed{" "}
                        {app.auditor_reviewed_at ? formatDate(app.auditor_reviewed_at) : "—"}
                      </p>
                    </div>
                    <Link href={`/gaira/applications/${app.id}`}>
                      <Button variant="secondary">View details</Button>
                    </Link>
                  </div>
                  <dl className="mb-4 grid gap-2 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-text-muted">Purpose</dt>
                      <dd>{app.purpose ?? "—"}</dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Audience</dt>
                      <dd>{app.audience ?? "—"}</dd>
                    </div>
                  </dl>
                  <div className="mb-4 rounded-md border border-border bg-background-secondary/50 p-3 text-sm">
                    <p className="mb-1 font-medium text-text-primary">Auditor feedback</p>
                    <p className="whitespace-pre-wrap text-text-secondary">
                      {app.auditor_feedback ?? "—"}
                    </p>
                  </div>
                  <FormField label="Rejection reason (if rejecting)">
                    <Textarea
                      value={rejectReasonByApp[app.id] ?? ""}
                      onChange={(e) =>
                        setRejectReasonByApp((prev) => ({ ...prev, [app.id]: e.target.value }))
                      }
                      placeholder="Required only if you reject this registration."
                      rows={3}
                    />
                  </FormField>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button onClick={() => void approve(app.id)} disabled={actingId === app.id}>
                      {actingId === app.id ? "Working…" : "Approve"}
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => void reject(app.id)}
                      disabled={actingId === app.id}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

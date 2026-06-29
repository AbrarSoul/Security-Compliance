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

export default function GairaReviewsPage() {
  return (
    <RequirePermission permission={PERMS.GAIRA_REVIEW}>
      <ReviewsContent />
    </RequirePermission>
  );
}

function ReviewsContent() {
  const [pending, setPending] = useState<AIApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [feedbackByApp, setFeedbackByApp] = useState<Record<string, string>>({});
  const [actingId, setActingId] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    gairaApi
      .listPendingAuditor()
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

  async function submitFeedback(applicationId: string) {
    const feedback = (feedbackByApp[applicationId] ?? "").trim();
    if (!feedback) {
      setError("Feedback is required before submitting to admin.");
      return;
    }
    setActingId(applicationId);
    setError("");
    setMessage("");
    try {
      const res = await gairaApi.submitAuditorFeedback(applicationId, feedback);
      setMessage(res.message);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to submit feedback");
    } finally {
      setActingId(null);
    }
  }

  return (
    <>
      <Header
        title="GAIRA registration reviews"
        subtitle="Review new AI applications and send feedback to admins"
      />
      <div className="page-container space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}

        <Card title="Awaiting auditor review">
          {loading ? (
            <TableSkeleton rows={4} />
          ) : pending.length === 0 ? (
            <EmptyState
              title="No pending registrations"
              description="New AI application registrations will appear here for your review."
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
                        Owner: {app.owner_name ?? "—"} · Registered {formatDate(app.created_at)}
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
                    <div>
                      <dt className="text-text-muted">AI provider</dt>
                      <dd>{app.ai_provider ?? "—"}</dd>
                    </div>
                    <div>
                      <dt className="text-text-muted">Technology</dt>
                      <dd>{app.technology_description ?? "—"}</dd>
                    </div>
                  </dl>
                  <FormField label="Feedback for admin" required>
                    <Textarea
                      value={feedbackByApp[app.id] ?? ""}
                      onChange={(e) =>
                        setFeedbackByApp((prev) => ({ ...prev, [app.id]: e.target.value }))
                      }
                      placeholder="Summarize your review, risks noticed, and recommendation for admin."
                      rows={4}
                    />
                  </FormField>
                  <div className="mt-3">
                    <Button
                      onClick={() => void submitFeedback(app.id)}
                      disabled={actingId === app.id}
                    >
                      {actingId === app.id ? "Submitting…" : "Send feedback to admin"}
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

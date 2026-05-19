"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { DecisionBadge } from "@/components/ui/DecisionBadge";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { modelsApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { ModelValidationResult } from "@/lib/types/sprint2";
import { formatDate, severityVariant } from "@/lib/utils";

export default function ModelValidationDetailPage() {
  return (
    <RequirePermission permission={PERMS.SCAN_READ}>
      <ValidationDetailContent />
    </RequirePermission>
  );
}

function ValidationDetailContent() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<ModelValidationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    modelsApi
      .getValidation(id)
      .then(setResult)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load validation")
      )
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <>
        <Header title="Validation history" />
        <div className="page-container">
          <TableSkeleton rows={4} />
        </div>
      </>
    );
  }

  if (error || !result) {
    return (
      <>
        <Header title="Validation history" />
        <div className="page-container">
          <Alert variant="error">{error ?? "Not found"}</Alert>
          <Link href="/models" className="mt-4 inline-block">
            <Button variant="secondary">Back</Button>
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Validation record"
        subtitle={`${result.model_name} · ${result.validated_at ? formatDate(result.validated_at) : ""}`}
      />
      <div className="page-container space-y-6">
        <Link href="/models">
          <Button variant="secondary">← Models</Button>
        </Link>

        <Card title="Risk summary">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <DecisionBadge decision={result.decision} />
            <Badge variant={severityVariant(result.risk_level)}>{result.risk_level}</Badge>
            <span className="font-mono text-lg font-bold">{result.risk_score}</span>
          </div>
          <p className="text-sm text-text-secondary">{result.primary_reason}</p>
          <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <span className="text-text-muted">Model type: </span>
              {result.model_type}
            </div>
            <div>
              <span className="text-text-muted">Provider: </span>
              {result.provider ?? "—"}
            </div>
            <div>
              <span className="text-text-muted">Classification: </span>
              {result.dataset_classification ?? "—"}
            </div>
          </dl>
        </Card>

        <Card title="Risk checks" description={`${result.risk_checks.length} checks`}>
          {result.risk_checks.length === 0 ? (
            <p className="text-sm text-text-muted">No risk checks recorded</p>
          ) : (
            <ul className="space-y-3">
              {result.risk_checks.map((c) => (
                <li key={c.code} className="rounded-lg border border-border p-4">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-text-primary">{c.title}</p>
                    <Badge variant={severityVariant(c.risk_level)}>{c.risk_level}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-text-muted">{c.description}</p>
                  <p className="mt-2 text-xs text-text-muted">Suggested: {c.suggested_action}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {result.recommendations.length > 0 && (
          <Card title="Recommendations">
            <ul className="list-inside list-disc text-sm text-text-secondary">
              {result.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </>
  );
}

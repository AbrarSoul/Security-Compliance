"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { modelsApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { ComplianceModel } from "@/lib/types/sprint2";
import { formatDate } from "@/lib/utils";

export default function ModelDetailPage() {
  return (
    <RequirePermission permission={PERMS.SCAN_READ}>
      <ModelDetailContent />
    </RequirePermission>
  );
}

function ModelDetailContent() {
  const { id } = useParams<{ id: string }>();
  const [model, setModel] = useState<ComplianceModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setModel(await modelsApi.get(id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load model");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const isLocal = model ? !model.data_leaves_platform : false;

  if (loading) {
    return (
      <>
        <Header title="Model details" />
        <div className="page-container">
          <TableSkeleton rows={4} />
        </div>
      </>
    );
  }

  if (error || !model) {
    return (
      <>
        <Header title="Model details" />
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
      <Header title={model.name} subtitle={model.code} />
      <div className="page-container space-y-6">
        <Link href="/models">
          <Button variant="secondary">← Models</Button>
        </Link>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Model profile">
            <dl className="space-y-3 text-sm">
              <Row label="Provider">{model.provider ?? "—"}</Row>
              <Row label="Type">
                <span className="capitalize">{model.model_type.replace(/_/g, " ")}</span>
              </Row>
              <Row label="Deployment">
                <Badge variant={isLocal ? "success" : "warning"}>
                  {isLocal ? "Local / on-platform" : "External"}
                </Badge>
              </Row>
              <Row label="Data leaves platform">
                {model.data_leaves_platform ? "Yes" : "No"}
              </Row>
              <Row label="Endpoint">{model.endpoint_url ?? "—"}</Row>
              <Row label="Retention policy">{model.data_retention_policy ?? "—"}</Row>
              <Row label="Logging">
                {model.logging_enabled == null ? "—" : model.logging_enabled ? "On" : "Off"}
              </Row>
            </dl>
          </Card>

          <Card title="Compliance status">
            <dl className="space-y-3 text-sm">
              <Row label="Approved">
                <Badge variant={model.is_approved ? "success" : "neutral"}>
                  {model.is_approved ? "Approved" : "Not approved"}
                </Badge>
              </Row>
              <Row label="Active">
                <Badge variant={model.is_active ? "success" : "neutral"}>
                  {model.is_active ? "Active" : "Inactive"}
                </Badge>
              </Row>
              <Row label="Registered">{formatDate(model.created_at)}</Row>
              <Row label="Updated">{formatDate(model.updated_at)}</Row>
            </dl>
            <p className="mt-4 text-xs text-text-muted">
              Run validation from the models page to generate risk summaries against a completed
              scan.
            </p>
          </Card>
        </div>
      </div>
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-text-muted">{label}</dt>
      <dd className="text-right font-medium text-text-primary">{children}</dd>
    </div>
  );
}

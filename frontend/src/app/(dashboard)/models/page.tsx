"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { DataTable } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Select } from "@/components/forms/Select";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { useAuth } from "@/contexts/AuthContext";
import { modelsApi, scansApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import type { ComplianceModel, ModelValidationResult } from "@/lib/types/sprint2";
import type { Scan } from "@/lib/types";
import { formatDate, severityVariant } from "@/lib/utils";
import { DecisionBadge } from "@/components/ui/DecisionBadge";

const MODEL_TYPES = [
  "local_model",
  "external_api",
  "cloud_hosted",
  "open_source",
  "proprietary",
];

export default function ModelsPage() {
  return (
    <RequirePermission permission={PERMS.SCAN_READ}>
      <ModelsContent />
    </RequirePermission>
  );
}

function ModelsContent() {
  const { canManagePolicies } = useAuth();
  const [typeFilter, setTypeFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [showValidate, setShowValidate] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<ModelValidationResult | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [saving, setSaving] = useState(false);

  const fetchPage = useMemo(
    () => (offset: number, limit: number) =>
      modelsApi.list({
        model_type: typeFilter || undefined,
        limit,
        offset,
      }),
    [typeFilter]
  );

  const { items, total, offset, setOffset, limit, loading, error, reload, resetPage } =
    usePaginatedList<ComplianceModel>(fetchPage, [typeFilter]);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canManagePolicies) return;
    setFormError(null);
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    try {
      await modelsApi.create({
        code: fd.get("code"),
        name: fd.get("name"),
        provider: fd.get("provider") || null,
        model_type: fd.get("model_type"),
        endpoint_url: fd.get("endpoint_url") || null,
        data_leaves_platform: fd.get("data_leaves_platform") === "true",
        is_approved: fd.get("is_approved") === "true",
        is_active: true,
      });
      setShowCreate(false);
      resetPage();
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to register model");
    } finally {
      setSaving(false);
    }
  }

  async function handleValidate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    setValidationResult(null);
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    try {
      const res = await modelsApi.validate({
        scan_id: String(fd.get("scan_id")),
        model_id: String(fd.get("model_id")),
      });
      setValidationResult(res);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Validation failed");
    } finally {
      setSaving(false);
    }
  }

  async function openValidate() {
    setShowValidate(true);
    const s = await scansApi.list();
    setScans(s.items.filter((scan) => scan.status === "completed"));
  }

  function isLocalModel(m: ComplianceModel) {
    return m.model_type === "local_model" || m.model_type === "open_source";
  }

  return (
    <>
      <Header
        title="Model validation"
        subtitle="Registered models, providers, and compliance risk summaries"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap gap-3">
          <FormField label="Model type">
            <Select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                resetPage();
              }}
            >
              <option value="">All types</option>
              {MODEL_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace(/_/g, " ")}
                </option>
              ))}
            </Select>
          </FormField>
          <Button variant="secondary" onClick={openValidate}>
            Run validation
          </Button>
          {canManagePolicies && (
            <Button onClick={() => setShowCreate((v) => !v)}>
              {showCreate ? "Cancel" : "Register model"}
            </Button>
          )}
        </div>

        {showCreate && canManagePolicies && (
          <Card title="Register model">
            {formError && (
              <div className="mb-4">
                <Alert variant="error">{formError}</Alert>
              </div>
            )}
            <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
              <FormField label="Code" required>
                <Input name="code" required />
              </FormField>
              <FormField label="Name" required>
                <Input name="name" required />
              </FormField>
              <FormField label="Provider">
                <Input name="provider" placeholder="OpenAI, internal, etc." />
              </FormField>
              <FormField label="Type" required>
                <Select name="model_type" required defaultValue="local_model">
                  {MODEL_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Endpoint URL">
                <Input name="endpoint_url" type="url" />
              </FormField>
              <FormField label="Data leaves platform">
                <Select name="data_leaves_platform" defaultValue="false">
                  <option value="false">No (local)</option>
                  <option value="true">Yes (external)</option>
                </Select>
              </FormField>
              <FormField label="Pre-approved">
                <Select name="is_approved" defaultValue="false">
                  <option value="false">No</option>
                  <option value="true">Yes</option>
                </Select>
              </FormField>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={saving}>
                  Register
                </Button>
              </div>
            </form>
          </Card>
        )}

        {showValidate && (
          <Card title="Validate model against scan">
            {formError && (
              <div className="mb-4">
                <Alert variant="error">{formError}</Alert>
              </div>
            )}
            <form onSubmit={handleValidate} className="grid max-w-md gap-4">
              <FormField label="Scan" required>
                <Select name="scan_id" required>
                  <option value="">Select…</option>
                  {scans.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id.slice(0, 8)}… — risk {s.risk_score}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Model" required>
                <Select name="model_id" required>
                  <option value="">Select…</option>
                  {items.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </Select>
              </FormField>
              <Button type="submit" disabled={saving}>
                Validate
              </Button>
            </form>
            {validationResult && (
              <div className="mt-6 rounded-lg border border-border bg-background-tertiary p-4">
                <div className="flex flex-wrap items-center gap-3">
                  <DecisionBadge decision={validationResult.decision} />
                  <Badge variant={severityVariant(validationResult.risk_level)}>
                    {validationResult.risk_level}
                  </Badge>
                  <span className="font-mono text-sm">
                    Score: {validationResult.risk_score}
                  </span>
                </div>
                <p className="mt-2 text-sm text-text-secondary">{validationResult.primary_reason}</p>
                <Link
                  href={`/models/validations/${validationResult.id}`}
                  className="mt-3 inline-block text-sm text-text-accent hover:underline"
                >
                  View full validation record →
                </Link>
              </div>
            )}
          </Card>
        )}

        <Card title="Registered models" description={`${total} models`}>
          <DataTable
            loading={loading}
            rows={items}
            emptyTitle="No models"
            emptyDescription="Register a compliance model to track validation history."
            columns={[
              {
                key: "name",
                header: "Name",
                render: (m) => (
                  <Link href={`/models/${m.id}`} className="font-medium text-text-accent hover:underline">
                    {m.name}
                  </Link>
                ),
              },
              {
                key: "provider",
                header: "Provider",
                render: (m) => m.provider ?? "—",
              },
              {
                key: "type",
                header: "Type",
                render: (m) => (
                  <span className="capitalize">{m.model_type.replace(/_/g, " ")}</span>
                ),
              },
              {
                key: "location",
                header: "Deployment",
                render: (m) => (
                  <Badge variant={isLocalModel(m) ? "success" : "warning"}>
                    {isLocalModel(m) ? "Local" : "External"}
                  </Badge>
                ),
              },
              {
                key: "approved",
                header: "Approved",
                render: (m) => (
                  <Badge variant={m.is_approved ? "success" : "neutral"}>
                    {m.is_approved ? "Yes" : "No"}
                  </Badge>
                ),
              },
              {
                key: "active",
                header: "Active",
                render: (m) => (
                  <Badge variant={m.is_active ? "success" : "neutral"}>
                    {m.is_active ? "Yes" : "No"}
                  </Badge>
                ),
              },
              {
                key: "updated",
                header: "Updated",
                render: (m) => formatDate(m.updated_at),
              },
            ]}
          />
          {!loading && total > limit && (
            <div className="mt-4">
              <Pagination total={total} limit={limit} offset={offset} onPageChange={setOffset} />
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

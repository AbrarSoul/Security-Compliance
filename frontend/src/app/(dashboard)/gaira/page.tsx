"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { DataTable } from "@/components/ui/DataTable";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Textarea } from "@/components/forms/Textarea";
import { Select } from "@/components/forms/Select";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { useAuth } from "@/contexts/AuthContext";
import { gairaApi, modelsApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { RoaiaRow } from "@/lib/types/gaira";
import type { ComplianceModel } from "@/lib/types/sprint2";
import { formatDate, flagVariant, statusLabel } from "@/lib/utils";
import { usePaginatedList } from "@/hooks/usePaginatedList";

export default function GairaPage() {
  return (
    <RequirePermission anyOf={[PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL]}>
      <GairaContent />
    </RequirePermission>
  );
}

function GairaContent() {
  const router = useRouter();
  const { hasPermission } = useAuth();
  const canManage = hasPermission(PERMS.GAIRA_MANAGE);
  const [showCreate, setShowCreate] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<ComplianceModel[]>([]);

  const fetchPage = useMemo(
    () => (offset: number, limit: number) =>
      gairaApi.listRoaia({ limit, offset }).then((res) => ({
        items: res.items,
        total: res.total,
      })),
    []
  );

  const { items, total, offset, setOffset, limit, loading, error, reload } =
    usePaginatedList<RoaiaRow>(fetchPage, []);

  async function openCreate() {
    setShowCreate(true);
    setFormError(null);
    try {
      const res = await modelsApi.list({ limit: 100 });
      setModels(res.items);
    } catch {
      setModels([]);
    }
  }

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!canManage) return;
    setFormError(null);
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    const modelId = String(fd.get("compliance_model_id") || "");
    try {
      const app = await gairaApi.createApplication({
        name: fd.get("name"),
        owner_name: fd.get("owner_name") || null,
        department: fd.get("department") || null,
        purpose: fd.get("purpose") || null,
        audience: fd.get("audience") || null,
        technology_description: fd.get("technology_description") || null,
        ai_provider: fd.get("ai_provider") || null,
        compliance_model_id: modelId || null,
      });
      setShowCreate(false);
      reload();
      router.push(`/gaira/applications/${app.id}`);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to register application");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Header
        title="GAIRA — AI risk assessment"
        subtitle="Register AI applications, run triage, and maintain the ROAIA inventory"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap gap-3">
          {canManage && (
            <Button onClick={() => (showCreate ? setShowCreate(false) : openCreate())}>
              {showCreate ? "Cancel" : "Register application"}
            </Button>
          )}
        </div>

        {showCreate && canManage && (
          <Card title="Register AI application">
            {formError && (
              <div className="mb-4">
                <Alert variant="error">{formError}</Alert>
              </div>
            )}
            <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
              <FormField label="Application name" required>
                <Input name="name" required placeholder="e.g. Meeting summarizer" />
              </FormField>
              <FormField label="Owner">
                <Input name="owner_name" placeholder="Application owner" />
              </FormField>
              <FormField label="Department">
                <Input name="department" />
              </FormField>
              <FormField label="Audience">
                <Input name="audience" placeholder="Who uses this system?" />
              </FormField>
              <FormField label="AI provider">
                <Input name="ai_provider" placeholder="e.g. GPT-Lab (TUNI)" />
              </FormField>
              <FormField label="Linked compliance model">
                <Select name="compliance_model_id" defaultValue="">
                  <option value="">None</option>
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name}
                    </option>
                  ))}
                </Select>
              </FormField>
              <div className="sm:col-span-2">
                <FormField label="Purpose">
                  <Textarea name="purpose" placeholder="What does this AI application do?" />
                </FormField>
              </div>
              <div className="sm:col-span-2">
                <FormField label="Technology / model">
                  <Textarea
                    name="technology_description"
                    placeholder="Model, deployment, integration details"
                  />
                </FormField>
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "Saving…" : "Register"}
                </Button>
              </div>
            </form>
          </Card>
        )}

        <Card title="ROAIA inventory" description={`${total} applications`}>
          <DataTable
            loading={loading}
            rows={items}
            emptyTitle="No AI applications"
            emptyDescription={
              canManage
                ? "Register an AI application to begin GAIRA assessment."
                : "No applications registered yet."
            }
            columns={[
              {
                key: "name",
                header: "Application",
                render: (row) => (
                  <Link
                    href={`/gaira/applications/${row.id}`}
                    className="font-medium text-text-accent hover:underline"
                  >
                    {row.name}
                  </Link>
                ),
              },
              { key: "owner", header: "Owner", render: (r) => r.owner_name ?? "—" },
              {
                key: "gaira",
                header: "GAIRA",
                render: (r) => (
                  <Badge variant={flagVariant(r.gaira_status)}>{statusLabel(r.gaira_status)}</Badge>
                ),
              },
              {
                key: "risk",
                header: "Risk level",
                render: (r) =>
                  r.risk_level ? (
                    <Badge variant={flagVariant(r.risk_level)}>{r.risk_level}</Badge>
                  ) : (
                    "—"
                  ),
              },
              {
                key: "provider",
                header: "Provider",
                render: (r) => r.ai_provider ?? "—",
              },
              {
                key: "next",
                header: "Next assessment",
                render: (r) =>
                  r.next_assessment_at ? formatDate(r.next_assessment_at) : "—",
              },
            ]}
          />
          {!loading && total > limit && (
            <div className="mt-4 flex gap-2">
              <Button
                variant="secondary"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - limit))}
              >
                Previous
              </Button>
              <Button
                variant="secondary"
                disabled={offset + limit >= total}
                onClick={() => setOffset(offset + limit)}
              >
                Next
              </Button>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

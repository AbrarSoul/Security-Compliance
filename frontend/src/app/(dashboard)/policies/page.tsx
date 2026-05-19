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
import { Textarea } from "@/components/forms/Textarea";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { useAuth } from "@/contexts/AuthContext";
import { policiesApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import type { CompliancePolicy } from "@/lib/types/sprint2";
import { formatDate, statusLabel } from "@/lib/utils";

const POLICY_TYPES = ["data_policy", "model_policy", "execution_policy", "security_policy"];

export default function PoliciesPage() {
  return (
    <RequirePermission anyOf={[PERMS.SCAN_READ, PERMS.POLICY_MANAGE]}>
      <PoliciesContent />
    </RequirePermission>
  );
}

function PoliciesContent() {
  const { canManagePolicies } = useAuth();
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchPage = useMemo(
    () => (offset: number, limit: number) =>
      policiesApi.list({
        status: statusFilter || undefined,
        limit,
        offset,
      }),
    [statusFilter]
  );

  const { items, total, offset, setOffset, limit, loading, error, reload, resetPage } =
    usePaginatedList<CompliancePolicy>(fetchPage, [statusFilter]);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    try {
      await policiesApi.create({
        name: fd.get("name"),
        description: fd.get("description") || null,
        policy_type: fd.get("policy_type"),
        status: "draft",
        priority: Number(fd.get("priority") || 0),
        thresholds: {
          block_below: Number(fd.get("block_below") || 40),
          warn_below: Number(fd.get("warn_below") || 70),
        },
      });
      setShowCreate(false);
      resetPage();
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create policy");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(policy: CompliancePolicy) {
    try {
      if (policy.status === "active") {
        await policiesApi.deactivate(policy.id);
      } else {
        await policiesApi.activate(policy.id);
      }
      reload();
    } catch {
      /* ignore */
    }
  }

  return (
    <>
      <Header
        title="Policy management"
        subtitle="Define compliance policies, thresholds, and attached rules"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap items-end gap-3">
          <FormField label="Status filter">
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                resetPage();
              }}
            >
              <option value="">All statuses</option>
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
            </Select>
          </FormField>
          {canManagePolicies && (
            <Button onClick={() => setShowCreate((v) => !v)}>
              {showCreate ? "Cancel" : "Create policy"}
            </Button>
          )}
        </div>

        {showCreate && canManagePolicies && (
          <Card title="New policy">
            {formError && (
              <div className="mb-4">
                <Alert variant="error">{formError}</Alert>
              </div>
            )}
            <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
              <FormField label="Name" required>
                <Input name="name" required />
              </FormField>
              <FormField label="Type" required>
                <Select name="policy_type" required defaultValue="execution_policy">
                  {POLICY_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {statusLabel(t)}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Priority" hint="0–1000">
                <Input name="priority" type="number" min={0} max={1000} defaultValue={0} />
              </FormField>
              <FormField label="Block below (risk score)">
                <Input name="block_below" type="number" min={0} max={100} defaultValue={40} />
              </FormField>
              <FormField label="Warn below (risk score)">
                <Input name="warn_below" type="number" min={0} max={100} defaultValue={70} />
              </FormField>
              <div className="sm:col-span-2">
                <FormField label="Description">
                  <Textarea name="description" rows={2} />
                </FormField>
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "Creating…" : "Create policy"}
                </Button>
              </div>
            </form>
          </Card>
        )}

        <Card title="Policies" description={`${total} total`}>
          <DataTable
            loading={loading}
            rows={items}
            emptyTitle="No policies"
            emptyDescription="Create a policy to group rules and set risk thresholds."
            columns={[
              {
                key: "name",
                header: "Name",
                render: (p) => (
                  <Link
                    href={`/policies/${p.id}`}
                    className="font-medium text-text-accent hover:underline"
                  >
                    {p.name}
                  </Link>
                ),
              },
              {
                key: "type",
                header: "Type",
                render: (p) => <span className="capitalize">{statusLabel(p.policy_type)}</span>,
              },
              {
                key: "status",
                header: "Status",
                render: (p) => <Badge variant="neutral">{statusLabel(p.status)}</Badge>,
              },
              {
                key: "thresholds",
                header: "Thresholds",
                render: (p) => (
                  <span className="font-mono text-xs text-text-muted">
                    block &lt; {p.thresholds.block_below} · warn &lt; {p.thresholds.warn_below}
                  </span>
                ),
              },
              {
                key: "rules",
                header: "Rules",
                render: (p) => <span>{p.rules?.length ?? 0}</span>,
              },
              {
                key: "updated",
                header: "Updated",
                render: (p) => formatDate(p.updated_at),
              },
              {
                key: "actions",
                header: "",
                render: (p) =>
                  canManagePolicies ? (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="text-xs"
                        onClick={() => toggleActive(p)}
                      >
                        {p.status === "active" ? "Deactivate" : "Activate"}
                      </Button>
                      <Link href={`/policies/${p.id}`}>
                        <Button variant="ghost" className="text-xs">
                          Details
                        </Button>
                      </Link>
                    </div>
                  ) : (
                    <Link href={`/policies/${p.id}`}>
                      <Button variant="outline" className="text-xs">
                        View
                      </Button>
                    </Link>
                  ),
              },
            ]}
          />
          {!loading && total > limit && (
            <div className="mt-4">
              <Pagination
                total={total}
                limit={limit}
                offset={offset}
                onPageChange={setOffset}
              />
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

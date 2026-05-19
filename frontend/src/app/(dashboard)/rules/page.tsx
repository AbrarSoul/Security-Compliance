"use client";

import { useMemo, useState } from "react";
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
import { rulesApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import type { ComplianceRule } from "@/lib/types/sprint2";
import { formatDate, severityVariant, statusLabel } from "@/lib/utils";

const CATEGORIES = ["data", "model", "execution", "security", "privacy"];
const SEVERITIES = ["low", "medium", "high", "critical"];
const ACTIONS = ["allow", "warn", "block"];

export default function RulesPage() {
  return (
    <RequirePermission anyOf={[PERMS.SCAN_READ, PERMS.RULE_MANAGE]}>
      <RulesContent />
    </RequirePermission>
  );
}

function RulesContent() {
  const { canManageRules } = useAuth();
  const [category, setCategory] = useState("");
  const [statusFilter, setStatusFilter] = useState<"" | "enabled" | "disabled">("");
  const [showCreate, setShowCreate] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const fetchPage = useMemo(
    () => async (offset: number, limit: number) => {
      const res = await rulesApi.list({
        category: category || undefined,
        enabled_only: statusFilter === "enabled" ? true : undefined,
        limit: 200,
        offset: 0,
      });
      let filtered = res.items;
      if (statusFilter === "disabled") {
        filtered = filtered.filter((r) => !r.is_enabled);
      }
      const page = filtered.slice(offset, offset + limit);
      return { items: page, total: filtered.length, limit, offset };
    },
    [category, statusFilter]
  );

  const { items, total, offset, setOffset, limit, loading, error, reload, resetPage } =
    usePaginatedList<ComplianceRule>(fetchPage, [category, statusFilter]);

  async function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setFormError(null);
    setSaving(true);
    const fd = new FormData(e.currentTarget);
    let condition: Record<string, unknown>;
    try {
      condition = JSON.parse(String(fd.get("condition") || "{}"));
    } catch {
      setFormError("Condition must be valid JSON");
      setSaving(false);
      return;
    }
    try {
      await rulesApi.create({
        code: fd.get("code"),
        name: fd.get("name"),
        description: fd.get("description") || null,
        category: fd.get("category"),
        severity: fd.get("severity"),
        action: fd.get("action"),
        priority: Number(fd.get("priority") || 0),
        condition,
        is_enabled: true,
      });
      setShowCreate(false);
      resetPage();
      reload();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Failed to create rule");
    } finally {
      setSaving(false);
    }
  }

  async function toggleRule(rule: ComplianceRule) {
    if (!canManageRules) return;
    try {
      if (rule.is_enabled) await rulesApi.disable(rule.id);
      else await rulesApi.enable(rule.id);
      reload();
    } catch {
      /* ignore */
    }
  }

  async function updateSeverity(rule: ComplianceRule, severity: string) {
    if (!canManageRules) return;
    try {
      await rulesApi.update(rule.id, { severity });
      reload();
    } catch {
      /* ignore */
    }
  }

  return (
    <>
      <Header
        title="Rule management"
        subtitle="Configure compliance rules, severity, and enforcement actions"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap items-end gap-3">
          <FormField label="Category">
            <Select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                resetPage();
              }}
            >
              <option value="">All categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {statusLabel(c)}
                </option>
              ))}
            </Select>
          </FormField>
          <FormField label="Status">
            <Select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as "" | "enabled" | "disabled");
                resetPage();
              }}
            >
              <option value="">All</option>
              <option value="enabled">Enabled</option>
              <option value="disabled">Disabled</option>
            </Select>
          </FormField>
          {canManageRules && (
            <Button onClick={() => setShowCreate((v) => !v)}>
              {showCreate ? "Cancel" : "Create rule"}
            </Button>
          )}
        </div>

        {showCreate && canManageRules && (
          <Card title="New rule">
            {formError && (
              <div className="mb-4">
                <Alert variant="error">{formError}</Alert>
              </div>
            )}
            <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
              <FormField label="Code" required>
                <Input name="code" required placeholder="RULE_PII_DETECTED" />
              </FormField>
              <FormField label="Name" required>
                <Input name="name" required />
              </FormField>
              <FormField label="Category" required>
                <Select name="category" required defaultValue="data">
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Severity" required>
                <Select name="severity" required defaultValue="medium">
                  {SEVERITIES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Action" required>
                <Select name="action" required defaultValue="warn">
                  {ACTIONS.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Priority">
                <Input name="priority" type="number" min={0} max={1000} defaultValue={0} />
              </FormField>
              <div className="sm:col-span-2">
                <FormField
                  label="Condition (JSON)"
                  hint='e.g. {"field":"risk_score","operator":"gte","value":60}'
                  required
                >
                  <Textarea
                    name="condition"
                    rows={3}
                    required
                    defaultValue='{"field":"risk_score","operator":"gte","value":60}'
                  />
                </FormField>
              </div>
              <div className="sm:col-span-2">
                <FormField label="Description">
                  <Textarea name="description" rows={2} />
                </FormField>
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={saving}>
                  {saving ? "Creating…" : "Create rule"}
                </Button>
              </div>
            </form>
          </Card>
        )}

        <Card title="Rules" description={`${total} matching`}>
          <DataTable
            loading={loading}
            rows={items}
            emptyTitle="No rules"
            emptyDescription="Adjust filters or create a new compliance rule."
            columns={[
              {
                key: "code",
                header: "Code",
                render: (r) => <span className="font-mono text-xs">{r.code}</span>,
              },
              { key: "name", header: "Name", render: (r) => r.name },
              {
                key: "category",
                header: "Category",
                render: (r) => <span className="capitalize">{r.category}</span>,
              },
              {
                key: "severity",
                header: "Severity",
                render: (r) =>
                  canManageRules ? (
                    <Select
                      className="!py-1 text-xs"
                      value={r.severity}
                      onChange={(e) => updateSeverity(r, e.target.value)}
                    >
                      {SEVERITIES.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    <Badge variant={severityVariant(r.severity)}>{r.severity}</Badge>
                  ),
              },
              {
                key: "action",
                header: "Action",
                render: (r) => <Badge variant="neutral">{r.action}</Badge>,
              },
              {
                key: "enabled",
                header: "Status",
                render: (r) => (
                  <Badge variant={r.is_enabled ? "success" : "neutral"}>
                    {r.is_enabled ? "Enabled" : "Disabled"}
                  </Badge>
                ),
              },
              {
                key: "updated",
                header: "Updated",
                render: (r) => formatDate(r.updated_at),
              },
              {
                key: "actions",
                header: "",
                render: (r) =>
                  canManageRules ? (
                    <Button
                      variant="outline"
                      className="text-xs"
                      onClick={() => toggleRule(r)}
                    >
                      {r.is_enabled ? "Disable" : "Enable"}
                    </Button>
                  ) : null,
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

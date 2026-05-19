"use client";

import { useMemo, useState } from "react";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Select } from "@/components/forms/Select";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { auditApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import type { AuditLogEntry } from "@/lib/types/sprint2";
import { formatDate, severityVariant } from "@/lib/utils";

export default function AuditLogsPage() {
  return (
    <RequirePermission permission={PERMS.AUDIT_READ}>
      <AuditLogsContent />
    </RequirePermission>
  );
}

function AuditLogsContent() {
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [severity, setSeverity] = useState("");
  const [sortDesc, setSortDesc] = useState(true);

  const fetchPage = useMemo(
    () => async (offset: number, limit: number) => {
      const res = await auditApi.list({
        action: action || undefined,
        severity: severity || undefined,
        limit: 200,
        offset: 0,
      });
      let filtered = res.items;
      if (search.trim()) {
        const q = search.toLowerCase();
        filtered = filtered.filter(
          (e) =>
            e.action.toLowerCase().includes(q) ||
            e.actor_email?.toLowerCase().includes(q) ||
            e.resource_type?.toLowerCase().includes(q)
        );
      }
      filtered = [...filtered].sort((a, b) => {
        const ta = new Date(a.created_at).getTime();
        const tb = new Date(b.created_at).getTime();
        return sortDesc ? tb - ta : ta - tb;
      });
      const page = filtered.slice(offset, offset + limit);
      return { items: page, total: filtered.length, limit, offset };
    },
    [search, action, severity, sortDesc]
  );

  const { items, total, offset, setOffset, limit, loading, error, resetPage } =
    usePaginatedList<AuditLogEntry>(fetchPage, [search, action, severity, sortDesc]);

  return (
    <>
      <Header
        title="Audit logs"
        subtitle="Searchable activity trail — auditor read-only access"
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <FormField label="Search">
            <Input
              placeholder="Action, user, resource…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                resetPage();
              }}
            />
          </FormField>
          <FormField label="Action">
            <Input
              placeholder="e.g. policy.create"
              value={action}
              onChange={(e) => {
                setAction(e.target.value);
                resetPage();
              }}
            />
          </FormField>
          <FormField label="Severity">
            <Select
              value={severity}
              onChange={(e) => {
                setSeverity(e.target.value);
                resetPage();
              }}
            >
              <option value="">All</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </Select>
          </FormField>
          <FormField label="Sort">
            <Select
              value={sortDesc ? "desc" : "asc"}
              onChange={(e) => {
                setSortDesc(e.target.value === "desc");
                resetPage();
              }}
            >
              <option value="desc">Newest first</option>
              <option value="asc">Oldest first</option>
            </Select>
          </FormField>
        </div>

        <Card title="Audit trail" description={`${total} entries`}>
          <DataTable
            loading={loading}
            rows={items}
            emptyTitle="No audit logs"
            emptyDescription="Adjust filters or check back after system activity."
            columns={[
              {
                key: "time",
                header: "Timestamp",
                render: (e) => (
                  <span className="whitespace-nowrap text-text-muted">
                    {formatDate(e.created_at)}
                  </span>
                ),
              },
              {
                key: "user",
                header: "User",
                render: (e) => e.actor_email ?? e.user_id?.slice(0, 8) ?? "—",
              },
              {
                key: "action",
                header: "Action",
                render: (e) => <span className="font-mono text-xs">{e.action}</span>,
              },
              {
                key: "resource",
                header: "Resource",
                render: (e) =>
                  e.resource_type ? (
                    <span className="text-xs">
                      {e.resource_type}
                      {e.resource_id ? ` · ${e.resource_id.slice(0, 8)}…` : ""}
                    </span>
                  ) : (
                    "—"
                  ),
              },
              {
                key: "severity",
                header: "Severity",
                render: (e) =>
                  e.severity ? (
                    <Badge variant={severityVariant(e.severity)}>{e.severity}</Badge>
                  ) : (
                    "—"
                  ),
              },
              {
                key: "status",
                header: "Status",
                render: (e) => <Badge variant="neutral">{e.status}</Badge>,
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

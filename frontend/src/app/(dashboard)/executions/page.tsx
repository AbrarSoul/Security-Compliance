"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { DataTable } from "@/components/ui/DataTable";
import { Pagination } from "@/components/ui/Pagination";
import { DecisionBadge, StatusBadge } from "@/components/ui/DecisionBadge";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { useAuth } from "@/contexts/AuthContext";
import { executionsApi } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import { usePaginatedList } from "@/hooks/usePaginatedList";
import type { ExecutionRequest } from "@/lib/types/sprint2";
import { formatDate, riskColor } from "@/lib/utils";

export default function ExecutionsPage() {
  return (
    <RequirePermission
      anyOf={[PERMS.EXECUTION_REQUEST, PERMS.EXECUTION_READ, PERMS.EXECUTION_READ_ALL]}
    >
      <ExecutionsContent />
    </RequirePermission>
  );
}

function ExecutionsContent() {
  const { canRequestExecution, isAuditor } = useAuth();
  const [statusFilter, setStatusFilter] = useState("");

  const fetchPage = useMemo(
    () => async (offset: number, limit: number) => {
      const res = await executionsApi.list({ limit: 200, offset: 0 });
      let filtered = res.items;
      if (statusFilter === "blocked") {
        filtered = filtered.filter(
          (e) =>
            e.status === "blocked" ||
            e.execution_result?.decision === "block"
        );
      } else if (statusFilter === "warning") {
        filtered = filtered.filter(
          (e) =>
            e.status.includes("warning") ||
            e.execution_result?.decision === "warn"
        );
      } else if (statusFilter) {
        filtered = filtered.filter((e) => e.status === statusFilter);
      }
      const page = filtered.slice(offset, offset + limit);
      return { items: page, total: filtered.length, limit, offset };
    },
    [statusFilter]
  );

  const { items, total, offset, setOffset, limit, loading, error, reload, resetPage } =
    usePaginatedList<ExecutionRequest>(fetchPage, [statusFilter]);

  return (
    <>
      <Header
        title="Execution status"
        subtitle={
          isAuditor
            ? "Read-only view of execution validation history"
            : "History, blocked runs, and warning acknowledgements"
        }
      />
      <div className="page-container space-y-6">
        {error && <Alert variant="error">{error}</Alert>}

        <div className="flex flex-wrap items-center gap-3">
          <select
            className="input-field w-auto"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              resetPage();
            }}
          >
            <option value="">All statuses</option>
            <option value="allowed">Allowed</option>
            <option value="blocked">Blocked</option>
            <option value="warning">Warnings</option>
            <option value="warning_pending_acknowledgement">Pending acknowledgement</option>
            <option value="approved_after_warning">Approved after warning</option>
            <option value="started">Started</option>
          </select>
          {canRequestExecution && (
            <Link href="/executions/validate">
              <Button>New validation</Button>
            </Link>
          )}
          <Button variant="secondary" onClick={reload}>
            Refresh
          </Button>
        </div>

        <Card title="Execution history" description={`${total} records`}>
          <DataTable
            loading={loading}
            rows={items}
            emptyTitle="No executions"
            emptyDescription="Run a pre-execution validation to see history here."
            emptyAction={
              canRequestExecution ? (
                <Link href="/executions/validate">
                  <Button>Validate execution</Button>
                </Link>
              ) : undefined
            }
            columns={[
              {
                key: "id",
                header: "Request",
                render: (e) => (
                  <Link
                    href={`/executions/${e.id}`}
                    className="font-mono text-xs text-text-accent hover:underline"
                  >
                    {e.id.slice(0, 8)}…
                  </Link>
                ),
              },
              {
                key: "model",
                header: "Model",
                render: (e) => e.model_name ?? e.compliance_model_id?.slice(0, 8) ?? "—",
              },
              {
                key: "status",
                header: "Status",
                render: (e) => <StatusBadge status={e.status} />,
              },
              {
                key: "decision",
                header: "Decision",
                render: (e) => <DecisionBadge decision={e.execution_result?.decision} />,
              },
              {
                key: "risk",
                header: "Risk",
                render: (e) => (
                  <span className={`font-mono font-bold ${riskColor(e.execution_result?.risk_score)}`}>
                    {e.execution_result?.risk_score ?? "—"}
                  </span>
                ),
              },
              {
                key: "created",
                header: "Created",
                render: (e) => formatDate(e.created_at),
              },
              {
                key: "actions",
                header: "",
                render: (e) => (
                  <Link href={`/executions/${e.id}`}>
                    <Button variant="outline" className="text-xs">
                      Details
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

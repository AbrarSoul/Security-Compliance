"use client";

import { Card } from "@/components/ui/Card";
import type { HighRiskModel, HighRiskUser } from "@/lib/types/analytics";

export function HighRiskUsersTable({ items }: { items: HighRiskUser[] }) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-border px-5 py-4">
        <h3 className="text-sm font-semibold text-text-primary">High-risk users</h3>
        <p className="mt-0.5 text-xs text-text-muted">By average prompt risk score</p>
      </div>
      {items.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-text-muted">No high-risk users in range</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-background-tertiary text-left text-xs uppercase text-text-muted">
                <th className="px-5 py-2.5">User</th>
                <th className="px-5 py-2.5">Scans</th>
                <th className="px-5 py-2.5">Blocked</th>
                <th className="px-5 py-2.5">Avg risk</th>
              </tr>
            </thead>
            <tbody>
              {items.map((u) => (
                <tr key={u.user_id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3">
                    <p className="font-medium text-text-secondary">{u.email}</p>
                    {u.full_name && <p className="text-xs text-text-muted">{u.full_name}</p>}
                  </td>
                  <td className="px-5 py-3 text-text-muted">{u.scan_count}</td>
                  <td className="px-5 py-3 text-text-muted">{u.blocked_prompts}</td>
                  <td className="px-5 py-3 font-mono font-medium text-accent-red">{u.avg_risk_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

export function HighRiskModelsTable({ items }: { items: HighRiskModel[] }) {
  return (
    <Card className="overflow-hidden p-0">
      <div className="border-b border-border px-5 py-4">
        <h3 className="text-sm font-semibold text-text-primary">High-risk models</h3>
        <p className="mt-0.5 text-xs text-text-muted">Models with blocked executions</p>
      </div>
      {items.length === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-text-muted">No high-risk models in range</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-background-tertiary text-left text-xs uppercase text-text-muted">
                <th className="px-5 py-2.5">Model</th>
                <th className="px-5 py-2.5">Provider</th>
                <th className="px-5 py-2.5">Executions</th>
                <th className="px-5 py-2.5">Blocked</th>
              </tr>
            </thead>
            <tbody>
              {items.map((m) => (
                <tr key={m.model_id} className="border-b border-border last:border-0">
                  <td className="px-5 py-3 font-medium text-text-secondary">{m.name}</td>
                  <td className="px-5 py-3 text-text-muted">{m.provider ?? "—"}</td>
                  <td className="px-5 py-3 text-text-muted">{m.execution_count}</td>
                  <td className="px-5 py-3 font-medium text-accent-red">{m.blocked_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

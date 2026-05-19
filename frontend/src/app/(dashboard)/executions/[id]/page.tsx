"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { DecisionBadge, StatusBadge } from "@/components/ui/DecisionBadge";
import { Badge } from "@/components/ui/Badge";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { Textarea } from "@/components/forms/Textarea";
import { FormField } from "@/components/forms/FormField";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { useAuth } from "@/contexts/AuthContext";
import { executionsApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { ExecutionRequest, ExecutionStatus } from "@/lib/types/sprint2";
import { formatDate, riskColor, severityVariant } from "@/lib/utils";

export default function ExecutionDetailPage() {
  return (
    <RequirePermission
      anyOf={[PERMS.EXECUTION_REQUEST, PERMS.EXECUTION_READ, PERMS.EXECUTION_READ_ALL]}
    >
      <ExecutionDetailContent />
    </RequirePermission>
  );
}

function ExecutionDetailContent() {
  const { id } = useParams<{ id: string }>();
  const { canRequestExecution, isAuditor } = useAuth();
  const [execution, setExecution] = useState<ExecutionRequest | null>(null);
  const [status, setStatus] = useState<ExecutionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [ackNote, setAckNote] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ex, st] = await Promise.all([
        executionsApi.get(id),
        executionsApi.getStatus(id),
      ]);
      setExecution(ex);
      setStatus(st);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load execution");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function acknowledge() {
    setBusy(true);
    setActionMsg(null);
    try {
      const res = await executionsApi.acknowledgeWarning(id, ackNote || undefined);
      setActionMsg(res.message);
      await load();
    } catch (err) {
      setActionMsg(err instanceof ApiError ? err.message : "Acknowledgement failed");
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    setBusy(true);
    setActionMsg(null);
    try {
      const res = await executionsApi.start(id);
      setActionMsg(res.message);
      await load();
    } catch (err) {
      setActionMsg(err instanceof ApiError ? err.message : "Start failed");
    } finally {
      setBusy(false);
    }
  }

  const evalSummary = execution?.evaluation_summary as Record<string, unknown> | null | undefined;
  const triggered = (evalSummary?.triggered_rules as Array<Record<string, string>>) ?? [];
  const violations = (evalSummary?.policy_violations as Array<Record<string, string>>) ?? [];

  if (loading) {
    return (
      <>
        <Header title="Execution details" />
        <div className="page-container">
          <TableSkeleton rows={5} />
        </div>
      </>
    );
  }

  if (error || !execution || !status) {
    return (
      <>
        <Header title="Execution details" />
        <div className="page-container">
          <Alert variant="error">{error ?? "Not found"}</Alert>
          <Link href="/executions" className="mt-4 inline-block">
            <Button variant="secondary">Back</Button>
          </Link>
        </div>
      </>
    );
  }

  const readOnly = isAuditor && !canRequestExecution;

  return (
    <>
      <Header
        title="Execution details"
        subtitle={execution.model_name ?? execution.execution_purpose ?? id.slice(0, 8)}
      />
      <div className="page-container space-y-6">
        <Link href="/executions">
          <Button variant="secondary">← History</Button>
        </Link>

        {actionMsg && <Alert variant="info">{actionMsg}</Alert>}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Status & decision">
            <dl className="space-y-3 text-sm">
              <Row label="Status">
                <StatusBadge status={status.status} />
              </Row>
              <Row label="Decision">
                <DecisionBadge decision={status.decision} />
              </Row>
              <Row label="Risk score">
                <span className={`font-mono font-bold ${riskColor(status.risk_score)}`}>
                  {status.risk_score ?? "—"}
                </span>
              </Row>
              <Row label="Risk level">{status.risk_level ?? "—"}</Row>
              <Row label="Can start">{status.can_start ? "Yes" : "No"}</Row>
              <Row label="Requires acknowledgement">
                {status.requires_acknowledgement ? "Yes" : "No"}
              </Row>
              {status.acknowledged_at && (
                <Row label="Acknowledged">{formatDate(status.acknowledged_at)}</Row>
              )}
              {status.started_at && (
                <Row label="Started">{formatDate(status.started_at)}</Row>
              )}
            </dl>
          </Card>

          <Card title="Enforcement">
            {status.blocking_reasons.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-semibold uppercase text-accent-red">Blocking</h4>
                <ul className="mt-1 list-inside list-disc text-sm text-text-secondary">
                  {status.blocking_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {status.warning_reasons.length > 0 && (
              <div className="mb-4">
                <h4 className="text-xs font-semibold uppercase text-accent-orange">Warnings</h4>
                <ul className="mt-1 list-inside list-disc text-sm text-text-secondary">
                  {status.warning_reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {status.explanation && (
              <p className="text-sm text-text-muted">{status.explanation}</p>
            )}
            {!readOnly && status.requires_acknowledgement && (
              <div className="mt-4 space-y-3 border-t border-border pt-4">
                <FormField label="Acknowledgement note">
                  <Textarea
                    value={ackNote}
                    onChange={(e) => setAckNote(e.target.value)}
                    rows={2}
                    placeholder="Document why you accept the risk…"
                  />
                </FormField>
                <Button onClick={acknowledge} disabled={busy}>
                  Acknowledge warning
                </Button>
              </div>
            )}
            {!readOnly && status.can_start && (
              <Button className="mt-4" onClick={start} disabled={busy}>
                Start execution
              </Button>
            )}
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Triggered rules" description={`${triggered.length} rules`}>
            {triggered.length === 0 ? (
              <p className="text-sm text-text-muted">None recorded</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {triggered.map((r, i) => (
                  <li key={i} className="rounded border border-border p-3">
                    <p className="font-medium">{r.rule_name ?? r.name}</p>
                    <p className="text-xs text-text-muted">{r.reason}</p>
                    {r.severity && (
                      <span className="mt-1 inline-block">
                        <Badge variant={severityVariant(r.severity)}>{r.severity}</Badge>
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title="Policy violations" description={`${violations.length} violations`}>
            {violations.length === 0 ? (
              <p className="text-sm text-text-muted">None recorded</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {violations.map((v, i) => (
                  <li key={i} className="rounded border border-border p-3">
                    <p className="font-medium">{v.policy_name ?? v.name}</p>
                    <p className="text-xs text-text-muted">{v.reason}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </div>

        {execution.recommendations && execution.recommendations.length > 0 && (
          <Card title="Recommendations">
            <ul className="list-inside list-disc text-sm text-text-secondary">
              {execution.recommendations.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-text-muted">{label}</dt>
      <dd className="text-right">{children}</dd>
    </div>
  );
}

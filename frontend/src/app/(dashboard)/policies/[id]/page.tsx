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
import { useAuth } from "@/contexts/AuthContext";
import { policiesApi, rulesApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type { CompliancePolicy, ComplianceRule } from "@/lib/types/sprint2";
import { formatDate, severityVariant, statusLabel } from "@/lib/utils";

export default function PolicyDetailPage() {
  return (
    <RequirePermission anyOf={[PERMS.SCAN_READ, PERMS.POLICY_MANAGE]}>
      <PolicyDetailContent />
    </RequirePermission>
  );
}

function PolicyDetailContent() {
  const { id } = useParams<{ id: string }>();
  const { canManagePolicies } = useAuth();
  const [policy, setPolicy] = useState<CompliancePolicy | null>(null);
  const [allRules, setAllRules] = useState<ComplianceRule[]>([]);
  const [selectedRuleIds, setSelectedRuleIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attachError, setAttachError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [p, rulesRes] = await Promise.all([
        policiesApi.get(id),
        rulesApi.list({ limit: 200 }),
      ]);
      setPolicy(p);
      setAllRules(rulesRes.items);
      const attached = new Set(p.rules.map((r) => r.id));
      setSelectedRuleIds(
        rulesRes.items.filter((r) => attached.has(r.id)).map((r) => r.id)
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load policy");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function saveRules() {
    if (!policy) return;
    setAttachError(null);
    const attached = new Set(policy.rules.map((r) => r.id));
    const selected = new Set(selectedRuleIds);
    const toAttach = selectedRuleIds.filter((rid) => !attached.has(rid));
    const toDetach = policy.rules.map((r) => r.id).filter((rid) => !selected.has(rid));
    try {
      if (toAttach.length) await policiesApi.attachRules(policy.id, toAttach);
      if (toDetach.length) await policiesApi.detachRules(policy.id, toDetach);
      await load();
    } catch (err) {
      setAttachError(err instanceof ApiError ? err.message : "Failed to update rules");
    }
  }

  async function toggleStatus() {
    if (!policy) return;
    try {
      if (policy.status === "active") await policiesApi.deactivate(policy.id);
      else await policiesApi.activate(policy.id);
      await load();
    } catch {
      /* ignore */
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Policy details" />
        <div className="page-container">
          <TableSkeleton rows={4} />
        </div>
      </>
    );
  }

  if (error || !policy) {
    return (
      <>
        <Header title="Policy details" />
        <div className="page-container">
          <Alert variant="error">{error ?? "Policy not found"}</Alert>
          <Link href="/policies" className="mt-4 inline-block">
            <Button variant="secondary">Back to policies</Button>
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title={policy.name}
        subtitle={`${statusLabel(policy.policy_type)} · ${statusLabel(policy.status)}`}
      />
      <div className="page-container space-y-6">
        <div className="flex flex-wrap gap-3">
          <Link href="/policies">
            <Button variant="secondary">← Policies</Button>
          </Link>
          {canManagePolicies && (
            <Button onClick={toggleStatus}>
              {policy.status === "active" ? "Deactivate" : "Activate"}
            </Button>
          )}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Overview">
            <dl className="space-y-3 text-sm">
              <Row label="Status">
                <Badge variant="neutral">{statusLabel(policy.status)}</Badge>
              </Row>
              <Row label="Priority">{policy.priority}</Row>
              <Row label="Active flag">{policy.is_active ? "Yes" : "No"}</Row>
              <Row label="Description">{policy.description ?? "—"}</Row>
              <Row label="Created">{formatDate(policy.created_at)}</Row>
            </dl>
          </Card>

          <Card title="Risk thresholds">
            <dl className="space-y-3 text-sm">
              <Row label="Block below">
                <span className="font-mono font-semibold text-accent-red">
                  {policy.thresholds.block_below}
                </span>
              </Row>
              <Row label="Warn below">
                <span className="font-mono font-semibold text-accent-orange">
                  {policy.thresholds.warn_below}
                </span>
              </Row>
              <p className="text-xs text-text-muted">
                Scores below block threshold result in block decisions; between block and warn
                thresholds trigger warnings.
              </p>
            </dl>
          </Card>
        </div>

        <Card title="Attached rules" description={`${policy.rules.length} rules linked`}>
          {policy.rules.length === 0 ? (
            <p className="text-sm text-text-muted">No rules attached yet.</p>
          ) : (
            <ul className="divide-y divide-border">
              {policy.rules.map((rule) => (
                <li key={rule.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-text-primary">{rule.name}</p>
                    <p className="text-xs text-text-muted">{rule.code}</p>
                  </div>
                  <Badge variant={severityVariant(rule.severity)}>{rule.severity}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {canManagePolicies && (
          <Card title="Manage rule attachments">
            {attachError && (
              <div className="mb-4">
                <Alert variant="error">{attachError}</Alert>
              </div>
            )}
            <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg border border-border p-3">
              {allRules.map((rule) => (
                <label
                  key={rule.id}
                  className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 hover:bg-background-tertiary"
                >
                  <input
                    type="checkbox"
                    checked={selectedRuleIds.includes(rule.id)}
                    onChange={(e) => {
                      setSelectedRuleIds((prev) =>
                        e.target.checked
                          ? [...prev, rule.id]
                          : prev.filter((rid) => rid !== rule.id)
                      );
                    }}
                  />
                  <span className="flex-1 text-sm">
                    <span className="font-medium">{rule.name}</span>
                    <span className="ml-2 text-text-muted">({rule.category})</span>
                  </span>
                  <Badge variant={rule.is_enabled ? "success" : "neutral"}>
                    {rule.is_enabled ? "On" : "Off"}
                  </Badge>
                </label>
              ))}
            </div>
            <Button className="mt-4" onClick={saveRules}>
              Save rule attachments
            </Button>
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
      <dd className="text-right font-medium text-text-primary">{children}</dd>
    </div>
  );
}

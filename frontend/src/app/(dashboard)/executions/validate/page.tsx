"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { DecisionBadge } from "@/components/ui/DecisionBadge";
import { Badge } from "@/components/ui/Badge";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Select } from "@/components/forms/Select";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { filesApi, scansApi, modelsApi, executionsApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import type {
  ComplianceModel,
  ValidateExecutionResponse,
} from "@/lib/types/sprint2";
import type { Scan, UploadedFile } from "@/lib/types";
import { formatDate, riskColor, severityVariant } from "@/lib/utils";

export default function ValidateExecutionPage() {
  return (
    <RequirePermission permission={PERMS.EXECUTION_REQUEST}>
      <ValidateExecutionContent />
    </RequirePermission>
  );
}

function ValidateExecutionContent() {
  const router = useRouter();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [models, setModels] = useState<ComplianceModel[]>([]);
  const [loadingOpts, setLoadingOpts] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ValidateExecutionResponse | null>(null);

  useEffect(() => {
    Promise.all([
      filesApi.list(),
      scansApi.list(),
      modelsApi.list({ active_only: true, limit: 100 }),
    ])
      .then(([f, s, m]) => {
        setFiles(f.items);
        setScans(s.items.filter((scan) => scan.status === "completed"));
        setModels(m.items);
      })
      .finally(() => setLoadingOpts(false));
  }, []);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setSubmitting(true);
    const fd = new FormData(e.currentTarget);
    const scanId = String(fd.get("scan_id"));
    const scan = scans.find((s) => s.id === scanId);
    if (!scan) {
      setError("Select a valid scan");
      setSubmitting(false);
      return;
    }
    try {
      const res = await executionsApi.validate({
        dataset_id: scan.file_id,
        scan_id: scanId,
        model_id: String(fd.get("model_id")),
        execution_purpose: String(fd.get("execution_purpose")),
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Validation failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Header
        title="Execution validation"
        subtitle="Pre-execution compliance check: rules, policies, and model risks"
      />
      <div className="page-container space-y-6">
        <Link href="/executions">
          <Button variant="secondary">← Execution history</Button>
        </Link>

        <Card title="Submit validation request">
          {loadingOpts ? (
            <p className="text-sm text-text-muted">Loading datasets and models…</p>
          ) : (
            <form onSubmit={handleSubmit} className="grid max-w-xl gap-4">
              {error && <Alert variant="error">{error}</Alert>}
              <FormField label="Completed scan" required>
                <Select name="scan_id" required defaultValue="">
                  <option value="" disabled>
                    Select scan…
                  </option>
                  {scans.map((scan) => {
                    const file = files.find((f) => f.id === scan.file_id);
                    return (
                      <option key={scan.id} value={scan.id}>
                        {file?.original_name ?? scan.id.slice(0, 8)} — risk {scan.risk_score ?? "?"}
                      </option>
                    );
                  })}
                </Select>
              </FormField>
              <FormField label="Compliance model" required>
                <Select name="model_id" required defaultValue="">
                  <option value="" disabled>
                    Select model…
                  </option>
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.model_type})
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Execution purpose" required>
                <Input
                  name="execution_purpose"
                  required
                  placeholder="e.g. Train classification model on customer data"
                />
              </FormField>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Validating…" : "Run validation"}
              </Button>
            </form>
          )}
        </Card>

        {result && (
          <ValidationResultCard
            result={result}
            onViewDetail={() => router.push(`/executions/${result.execution_request_id}`)}
          />
        )}
      </div>
    </>
  );
}

function ValidationResultCard({
  result,
  onViewDetail,
}: {
  result: ValidateExecutionResponse;
  onViewDetail: () => void;
}) {
  return (
    <Card title="Validation result">
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <DecisionBadge decision={result.decision} />
        <span className={`text-2xl font-mono font-bold ${riskColor(result.risk_score)}`}>
          {result.risk_score}
        </span>
        <Badge variant={severityVariant(result.risk_level)}>{`${result.risk_level} risk`}</Badge>
        <span className="text-sm text-text-muted">{formatDate(result.validated_at)}</span>
      </div>

      <p className="mb-6 text-sm text-text-secondary">{result.explanation}</p>

      <div className="grid gap-6 lg:grid-cols-3">
        <Section title="Triggered rules" count={result.triggered_rules.length}>
          {result.triggered_rules.length === 0 ? (
            <p className="text-sm text-text-muted">None</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {result.triggered_rules.map((r) => (
                <li key={r.rule_id} className="rounded-lg border border-border p-3">
                  <p className="font-medium">{r.rule_name}</p>
                  <p className="text-xs text-text-muted">{r.reason}</p>
                  <span className="mt-1 inline-block">
                    <Badge variant={severityVariant(r.severity)}>{r.severity}</Badge>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Policy violations" count={result.policy_violations.length}>
          {result.policy_violations.length === 0 ? (
            <p className="text-sm text-text-muted">None</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {result.policy_violations.map((v) => (
                <li key={v.policy_id} className="rounded-lg border border-border p-3">
                  <p className="font-medium">{v.policy_name}</p>
                  <p className="text-xs text-text-muted">{v.reason}</p>
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Model risks" count={result.model_risks.length}>
          {result.model_risks.length === 0 ? (
            <p className="text-sm text-text-muted">None</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {result.model_risks.map((m) => (
                <li key={m.code} className="rounded-lg border border-border p-3">
                  <p className="font-medium">{m.title}</p>
                  <p className="text-xs text-text-muted">{m.description}</p>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>

      {result.recommendations.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-text-primary">Recommendations</h4>
          <ul className="mt-2 list-inside list-disc text-sm text-text-muted">
            {result.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <Button className="mt-6" onClick={onViewDetail}>
        View execution details
      </Button>
    </Card>
  );
}

function Section({
  title,
  count,
  children,
}: {
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <div>
      <h4 className="mb-2 text-sm font-semibold text-text-primary">
        {title} <span className="text-text-muted">({count})</span>
      </h4>
      {children}
    </div>
  );
}

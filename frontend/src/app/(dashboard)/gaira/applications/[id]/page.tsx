"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { DataTable } from "@/components/ui/DataTable";
import { FormField } from "@/components/forms/FormField";
import { Select } from "@/components/forms/Select";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { gairaApi, scansApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import {
  ASSESSMENT_TYPE_LABELS,
  REGISTRATION_STATUS_LABELS,
  type AIApplication,
  type GairaAssessment,
  type GairaModuleSummary,
} from "@/lib/types/gaira";
import type { Scan } from "@/lib/types";
import { formatDate, flagVariant, statusLabel } from "@/lib/utils";

export default function GairaApplicationPage() {
  return (
    <RequirePermission anyOf={[PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL]}>
      <ApplicationContent />
    </RequirePermission>
  );
}

function ApplicationContent() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { hasPermission } = useAuth();
  const canManage = hasPermission(PERMS.GAIRA_MANAGE);
  const [application, setApplication] = useState<AIApplication | null>(null);
  const [assessments, setAssessments] = useState<GairaAssessment[]>([]);
  const [modules, setModules] = useState<GairaModuleSummary[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [showStart, setShowStart] = useState(false);
  const [assessmentType, setAssessmentType] = useState("ai_risk_levels");
  const [scanId, setScanId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [app, assess, framework, scanList] = await Promise.all([
        gairaApi.getApplication(id),
        gairaApi.listAssessments(id),
        gairaApi.getFramework(),
        scansApi.list(),
      ]);
      setApplication(app);
      setAssessments(assess.items);
      setModules(framework.modules);
      setScans(scanList.items.filter((s) => s.status === "completed"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load application");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleStartAssessment(e: React.FormEvent) {
    e.preventDefault();
    if (!canManage) return;
    setStarting(true);
    setError(null);
    try {
      const assessment = await gairaApi.startAssessment(id, {
        assessment_type: assessmentType,
        scan_id: scanId || undefined,
      });
      router.push(`/gaira/assessments/${assessment.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start assessment");
    } finally {
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="AI application" />
        <div className="page-container">
          <TableSkeleton rows={4} />
        </div>
      </>
    );
  }

  if (error && !application) {
    return (
      <>
        <Header title="AI application" />
        <div className="page-container">
          <Alert variant="error">{error}</Alert>
          <Link href="/gaira" className="mt-4 inline-block">
            <Button variant="secondary">← ROAIA</Button>
          </Link>
        </div>
      </>
    );
  }

  if (!application) return null;

  const isApproved = application.registration_status === "approved";
  const registrationLabel =
    REGISTRATION_STATUS_LABELS[application.registration_status] ??
    application.registration_status;

  return (
    <>
      <Header title={application.name} subtitle="AI application & GAIRA assessments" />
      <div className="page-container space-y-6">
        <Link href="/gaira">
          <Button variant="secondary">← ROAIA inventory</Button>
        </Link>

        {error && <Alert variant="error">{error}</Alert>}

        {!isApproved && (
          <Alert variant={application.registration_status === "rejected" ? "error" : "info"}>
            <p className="font-medium">Registration status: {registrationLabel}</p>
            {application.registration_status === "pending_auditor" && (
              <p className="mt-1 text-sm opacity-90">
                Your application is waiting for an auditor to review it. Assessments are locked
                until admin approval.
              </p>
            )}
            {application.registration_status === "pending_admin" && (
              <p className="mt-1 text-sm opacity-90">
                Auditor review is complete. An admin will approve or reject this application soon.
              </p>
            )}
            {application.registration_status === "pending_admin" && application.auditor_feedback && (
              <p className="mt-2 text-sm opacity-90">
                <span className="font-medium">Auditor feedback:</span> {application.auditor_feedback}
              </p>
            )}
            {application.registration_status === "rejected" && application.rejection_reason && (
              <p className="mt-1 text-sm opacity-90">
                Reason: {application.rejection_reason}
              </p>
            )}
          </Alert>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Application profile">
            <dl className="space-y-3 text-sm">
              <Row label="Owner">{application.owner_name ?? "—"}</Row>
              <Row label="Department">{application.department ?? "—"}</Row>
              <Row label="Purpose">{application.purpose ?? "—"}</Row>
              <Row label="Audience">{application.audience ?? "—"}</Row>
              <Row label="AI provider">{application.ai_provider ?? "—"}</Row>
              <Row label="Technology">{application.technology_description ?? "—"}</Row>
            </dl>
          </Card>

          <Card title="GAIRA status">
            <dl className="space-y-3 text-sm">
              <Row label="Registration">
                <Badge variant={flagVariant(application.registration_status)}>
                  {registrationLabel}
                </Badge>
              </Row>
              <Row label="GAIRA status">
                <Badge variant={flagVariant(application.gaira_status)}>
                  {statusLabel(application.gaira_status)}
                </Badge>
              </Row>
              <Row label="Risk level">
                {application.risk_level ? (
                  <Badge variant={flagVariant(application.risk_level)}>
                    {application.risk_level}
                  </Badge>
                ) : (
                  "—"
                )}
              </Row>
              <Row label="Compliance check">
                <Badge variant={flagVariant(application.compliance_check_status)}>
                  {statusLabel(application.compliance_check_status)}
                </Badge>
              </Row>
              <Row label="DPIA">{statusLabel(application.dpia_status)}</Row>
              <Row label="Registered">{formatDate(application.created_at)}</Row>
            </dl>
          </Card>
        </div>

        <div className="flex flex-wrap gap-3">
          {canManage && isApproved && (
            <Button onClick={() => setShowStart((v) => !v)}>
              {showStart ? "Cancel" : "Start assessment"}
            </Button>
          )}
        </div>

        {showStart && canManage && isApproved && (
          <Card title="Start new assessment">
            <form onSubmit={handleStartAssessment} className="grid max-w-lg gap-4">
              <FormField label="Assessment module" required>
                <Select
                  value={assessmentType}
                  onChange={(e) => setAssessmentType(e.target.value)}
                  required
                >
                  {modules.map((m) => (
                    <option key={m.key} value={m.key}>
                      {ASSESSMENT_TYPE_LABELS[m.key] ?? m.title} ({m.question_count} questions)
                    </option>
                  ))}
                </Select>
              </FormField>
              <FormField label="Link scan (optional, for prefill)">
                <Select value={scanId} onChange={(e) => setScanId(e.target.value)}>
                  <option value="">None</option>
                  {scans.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.id.slice(0, 8)}… — risk {s.risk_score}
                    </option>
                  ))}
                </Select>
              </FormField>
              <p className="text-xs text-text-muted">
                Tip: start with <strong>AI Risk Levels</strong> for triage, then GAIRA Light or
                Comprehensive based on the result.
              </p>
              <Button type="submit" disabled={starting}>
                {starting ? "Starting…" : "Start assessment"}
              </Button>
            </form>
          </Card>
        )}

        <Card title="Assessments" description={`${assessments.length} total`}>
          <DataTable
            rows={assessments}
            emptyTitle="No assessments yet"
            emptyDescription={
              canManage && isApproved
                ? "Start an assessment to evaluate this application."
                : !isApproved
                  ? "Assessments unlock after admin approval."
                  : undefined
            }
            columns={[
              {
                key: "type",
                header: "Module",
                render: (a) =>
                  ASSESSMENT_TYPE_LABELS[a.assessment_type] ?? a.assessment_type,
              },
              {
                key: "status",
                header: "Status",
                render: (a) => (
                  <Badge variant={flagVariant(a.status)}>{statusLabel(a.status)}</Badge>
                ),
              },
              {
                key: "risk",
                header: "Risk",
                render: (a) => a.overall_risk_level ?? "—",
              },
              {
                key: "updated",
                header: "Updated",
                render: (a) => formatDate(a.updated_at),
              },
              {
                key: "action",
                header: "",
                render: (a) => (
                  <Link href={`/gaira/assessments/${a.id}`}>
                    <Button variant="secondary">
                      {a.status === "draft" && canManage ? "Continue" : "View"}
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        </Card>
      </div>
    </>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-4">
      <dt className="w-36 shrink-0 text-text-muted">{label}</dt>
      <dd className="text-text-primary">{children}</dd>
    </div>
  );
}

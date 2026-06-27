"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { FormField } from "@/components/forms/FormField";
import { Input } from "@/components/forms/Input";
import { Textarea } from "@/components/forms/Textarea";
import { Select } from "@/components/forms/Select";
import { RequirePermission } from "@/components/rbac/RequirePermission";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { useAuth } from "@/contexts/AuthContext";
import { gairaApi, ApiError } from "@/lib/api";
import { PERMS } from "@/lib/permissions";
import {
  ASSESSMENT_TYPE_LABELS,
  RISK_LEVEL_OPTIONS,
  type GairaAnswer,
  type GairaAssessment,
  type GairaModuleDetail,
  type GairaQuestion,
} from "@/lib/types/gaira";
import { formatDate, flagVariant, statusLabel } from "@/lib/utils";

export default function GairaAssessmentPage() {
  return (
    <RequirePermission anyOf={[PERMS.GAIRA_READ, PERMS.GAIRA_READ_ALL]}>
      <AssessmentContent />
    </RequirePermission>
  );
}

function AssessmentContent() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { hasPermission } = useAuth();
  const canManage = hasPermission(PERMS.GAIRA_MANAGE);
  const [assessment, setAssessment] = useState<GairaAssessment | null>(null);
  const [module, setModule] = useState<GairaModuleDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, GairaAnswer>>({});
  const [activeStep, setActiveStep] = useState("1");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [computing, setComputing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [overallRisk, setOverallRisk] = useState("");
  const [proceedDecision, setProceedDecision] = useState("");
  const [decisionComments, setDecisionComments] = useState("");

  const isDraft = assessment?.status === "draft";
  const readOnly = !canManage || !isDraft;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const a = await gairaApi.getAssessment(id);
      const mod = await gairaApi.getModule(a.assessment_type);
      setAssessment(a);
      setModule(mod);
      setAnswers(a.answers_json ?? {});
      setOverallRisk(a.overall_risk_level ?? a.computed_json?.risk_level ?? "");
      setProceedDecision(a.proceed_decision ?? "");
      setDecisionComments(a.decision_comments ?? "");
      const firstStep = mod.steps[0]?.id ?? "1";
      setActiveStep(firstStep);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load assessment");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const stepQuestions = useMemo(() => {
    if (!module) return [];
    return module.questions.filter((q) => q.step_id === activeStep);
  }, [module, activeStep]);

  function setAnswer(questionId: string, patch: Partial<GairaAnswer>) {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: { ...prev[questionId], ...patch },
    }));
  }

  async function saveAnswers() {
    if (!assessment || readOnly) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await gairaApi.updateAnswers(assessment.id, answers, true);
      setAssessment(updated);
      setAnswers(updated.answers_json ?? {});
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save answers");
    } finally {
      setSaving(false);
    }
  }

  async function runCompute() {
    if (!assessment) return;
    setComputing(true);
    setError(null);
    try {
      if (!readOnly) await gairaApi.updateAnswers(assessment.id, answers, true);
      const updated = await gairaApi.compute(assessment.id);
      setAssessment(updated);
      setAnswers(updated.answers_json ?? {});
      if (updated.computed_json?.risk_level) {
        setOverallRisk(updated.computed_json.risk_level);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Compute failed");
    } finally {
      setComputing(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!assessment || readOnly) return;
    setSubmitting(true);
    setError(null);
    try {
      await gairaApi.updateAnswers(assessment.id, answers, true);
      const updated = await gairaApi.submit(assessment.id, {
        overall_risk_level: overallRisk || undefined,
        proceed_decision: proceedDecision || undefined,
        decision_comments: decisionComments || undefined,
      });
      setAssessment(updated);
      router.push(`/gaira/applications/${updated.application_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Submit failed");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="GAIRA assessment" />
        <div className="page-container">
          <TableSkeleton rows={6} />
        </div>
      </>
    );
  }

  if (!assessment || !module) {
    return (
      <>
        <Header title="GAIRA assessment" />
        <div className="page-container">
          <Alert variant="error">{error ?? "Assessment not found"}</Alert>
        </div>
      </>
    );
  }

  const computed = assessment.computed_json;
  const needsSecondLine = computed?.flags?.includes("second_line_required");

  return (
    <>
      <Header
        title={ASSESSMENT_TYPE_LABELS[assessment.assessment_type] ?? module.title}
        subtitle={`Assessment · ${statusLabel(assessment.status)}`}
      />
      <div className="page-container space-y-6">
        <div className="flex flex-wrap gap-3">
          <Link href={`/gaira/applications/${assessment.application_id}`}>
            <Button variant="secondary">← Application</Button>
          </Link>
          {!readOnly && (
            <>
              <Button variant="secondary" onClick={() => void saveAnswers()} disabled={saving}>
                {saving ? "Saving…" : "Save answers"}
              </Button>
              <Button variant="secondary" onClick={() => void runCompute()} disabled={computing}>
                {computing ? "Computing…" : "Compute recommendations"}
              </Button>
            </>
          )}
        </div>

        {error && <Alert variant="error">{error}</Alert>}

        {computed && (
          <Alert variant="info">
            <p className="font-medium">
              {computed.risk_level && (
                <span className="mr-2">
                  Suggested risk: <Badge variant={flagVariant(computed.risk_level)}>{computed.risk_level}</Badge>
                </span>
              )}
              {computed.recommended_module && (
                <span className="mr-2">
                  Next module: {ASSESSMENT_TYPE_LABELS[computed.recommended_module] ?? computed.recommended_module}
                </span>
              )}
            </p>
            {computed.proceed_recommendation && (
              <p className="mt-1 text-sm opacity-90">{computed.proceed_recommendation}</p>
            )}
            {needsSecondLine && (
              <p className="mt-2 text-sm text-accent-amber">
                Second-line review required on flagged Step 4 answers before submit.
              </p>
            )}
          </Alert>
        )}

        {module.steps.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {module.steps.map((step) => (
              <Button
                key={step.id}
                variant={activeStep === step.id ? "primary" : "secondary"}
                onClick={() => setActiveStep(step.id)}
              >
                Step {step.id}
              </Button>
            ))}
          </div>
        )}

        <Card
          title={module.steps.find((s) => s.id === activeStep)?.title ?? `Step ${activeStep}`}
          description={`${stepQuestions.length} questions in this step`}
        >
          <div className="space-y-6">
            {stepQuestions.map((q) => (
              <QuestionField
                key={q.id}
                question={q}
                answer={answers[q.id]}
                readOnly={readOnly}
                onChange={(patch) => setAnswer(q.id, patch)}
              />
            ))}
            {stepQuestions.length === 0 && (
              <p className="text-sm text-text-muted">No questions in this step.</p>
            )}
          </div>
        </Card>

        {(isDraft && canManage) || assessment.status === "submitted" ? (
          <Card title="Decision & submit">
            {readOnly ? (
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-text-muted">Overall risk</dt>
                  <dd>{assessment.overall_risk_level ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Proceed decision</dt>
                  <dd>{assessment.proceed_decision ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-text-muted">Comments</dt>
                  <dd>{assessment.decision_comments ?? "—"}</dd>
                </div>
                {assessment.submitted_at && (
                  <div>
                    <dt className="text-text-muted">Submitted</dt>
                    <dd>{formatDate(assessment.submitted_at)}</dd>
                  </div>
                )}
              </dl>
            ) : (
              <form onSubmit={handleSubmit} className="grid max-w-lg gap-4">
                <FormField label="Overall risk level">
                  <Select
                    value={overallRisk}
                    onChange={(e) => setOverallRisk(e.target.value)}
                  >
                    <option value="">Select…</option>
                    {RISK_LEVEL_OPTIONS.map((r) => (
                      <option key={r} value={r}>
                        {r.replace(/_/g, " ")}
                      </option>
                    ))}
                  </Select>
                </FormField>
                <FormField label="Proceed decision">
                  <Input
                    value={proceedDecision}
                    onChange={(e) => setProceedDecision(e.target.value)}
                    placeholder="e.g. Proceed with conditions"
                  />
                </FormField>
                <FormField label="Decision comments">
                  <Textarea
                    value={decisionComments}
                    onChange={(e) => setDecisionComments(e.target.value)}
                    placeholder="Stakeholder notes, conditions, next steps"
                  />
                </FormField>
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Submitting…" : "Submit assessment"}
                </Button>
              </form>
            )}
          </Card>
        ) : null}
      </div>
    </>
  );
}

function QuestionField({
  question,
  answer,
  readOnly,
  onChange,
}: {
  question: GairaQuestion;
  answer?: GairaAnswer;
  readOnly: boolean;
  onChange: (patch: Partial<GairaAnswer>) => void;
}) {
  const isBoolean = question.answer_type === "boolean";
  const value = answer?.value != null ? String(answer.value) : "";
  const source = answer?.source;

  return (
    <div className="rounded-lg border border-border bg-background-tertiary/40 p-4">
      <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
        <p className="text-sm font-medium text-text-primary">
          <span className="font-mono text-text-muted">{question.id}</span> — {question.text}
        </p>
        {source && (
          <Badge variant="info">{`Prefilled: ${source}`}</Badge>
        )}
        {answer?.flagged && (
          <Badge variant="warning">Flagged — 2nd line review</Badge>
        )}
      </div>
      {question.explanation && (
        <p className="mb-3 text-xs text-text-muted">{question.explanation}</p>
      )}

      {isBoolean ? (
        <Select
          value={value}
          disabled={readOnly}
          onChange={(e) => onChange({ value: e.target.value, source: "user" })}
        >
          <option value="">Select…</option>
          <option value="Yes">Yes</option>
          <option value="No">No</option>
        </Select>
      ) : (
        <Textarea
          value={value}
          disabled={readOnly}
          onChange={(e) => onChange({ value: e.target.value, source: "user" })}
          placeholder="Your answer"
        />
      )}

      {!readOnly && answer?.flagged && (
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <FormField label="Second-line reviewer" hint="Required for flagged answers">
            <Input
              value={answer.second_line_reviewer ?? ""}
              onChange={(e) => onChange({ second_line_reviewer: e.target.value })}
              placeholder="legal@company.com"
            />
          </FormField>
          <FormField label="Second-line comment">
            <Input
              value={answer.second_line_comment ?? ""}
              onChange={(e) => onChange({ second_line_comment: e.target.value })}
            />
          </FormField>
        </div>
      )}
    </div>
  );
}

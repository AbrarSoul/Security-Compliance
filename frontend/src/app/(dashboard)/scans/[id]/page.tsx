"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { ComplianceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { RiskScoreGauge } from "@/components/scans/RiskScoreGauge";
import { ScanExecutiveSummary } from "@/components/scans/ScanExecutiveSummary";
import { ScanScoreBreakdown } from "@/components/scans/ScanScoreBreakdown";
import { FindingCard } from "@/components/scans/FindingCard";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { filesApi, reportsApi, scansApi, triggerDownload, ApiError } from "@/lib/api";
import type { Scan, UploadedFile } from "@/lib/types";
import { groupFindingsBySeverity, groupRecommendationsByPriority, riskBandLabel } from "@/lib/scanReport";
import { formatDate, statusLabel } from "@/lib/utils";

export default function ScanDetailPage() {
  const params = useParams();
  const scanId = params.id as string;
  const [scan, setScan] = useState<Scan | null>(null);
  const [file, setFile] = useState<UploadedFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState<"json" | "pdf" | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    scansApi
      .get(scanId)
      .then(async (s) => {
        setScan(s);
        const f = await filesApi.get(s.file_id);
        setFile(f);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [scanId]);

  async function handleGenerateReport() {
    if (!scan) return;
    setGenerating(true);
    setError("");
    try {
      const res = await reportsApi.generate(scan.id);
      const blob = await reportsApi.download(res.report.id, "pdf");
      triggerDownload(blob, `compliance-report-${res.report.id}.pdf`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Report generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function handleDownload(format: "json" | "pdf") {
    setDownloading(format);
    try {
      const res = await reportsApi.generate(scan!.id);
      const blob = await reportsApi.download(res.report.id, format);
      triggerDownload(blob, `compliance-report-${res.report.id}.${format}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  }

  if (loading) {
    return (
      <>
        <Header title="Scan report" />
        <div className="page-container">
          <div className="grid gap-4 lg:grid-cols-3">
            <StatCardSkeleton />
            <div className="lg:col-span-2 space-y-4">
              <StatCardSkeleton />
            </div>
          </div>
        </div>
      </>
    );
  }

  if (!scan) {
    return (
      <>
        <Header title="Scan report" />
        <div className="page-container">
          <Alert variant="error">{error || "Scan not found"}</Alert>
        </div>
      </>
    );
  }

  const findings = scan.findings ?? [];
  const recommendations = scan.recommendations ?? [];
  const findingsBySeverity = groupFindingsBySeverity(findings);
  const recsByPriority = groupRecommendationsByPriority(recommendations);

  return (
    <>
      <Header
        title="Scan report"
        subtitle={file?.original_name ?? `Scan ${scan.id.slice(0, 8)}`}
      />
      <div className="page-container animate-fade-in space-y-6">
        <Link
          href="/scans"
          className="inline-flex items-center gap-1 text-sm font-medium text-text-accent hover:text-primary transition-colors"
        >
          ← Back to scans
        </Link>

        {error && <Alert variant="error">{error}</Alert>}

        <Card title="Executive summary">
          <ScanExecutiveSummary
            complianceStatus={scan.compliance_status}
            classification={scan.classification}
            findingsCount={findings.length}
            file={file}
            startedAt={scan.started_at}
            completedAt={scan.completed_at}
          />
        </Card>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card title="Risk assessment">
            <div className="flex flex-col items-center py-4">
              <RiskScoreGauge score={scan.risk_score} />
              <p className="mt-2 text-sm font-medium text-text-muted">{riskBandLabel(scan.risk_score)}</p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                <ComplianceBadge status={scan.compliance_status} />
                {scan.classification && (
                  <span className="rounded-md bg-surface-elevated px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {scan.classification}
                  </span>
                )}
              </div>
            </div>
          </Card>

          <div className="lg:col-span-2">
            <Card title="Scan details">
              <dl className="grid gap-4 text-sm sm:grid-cols-2">
                <Info label="File" value={file?.original_name ?? scan.file_id} />
                <Info label="Status" value={statusLabel(scan.status)} />
                <Info label="Started" value={scan.started_at ? formatDate(scan.started_at) : "—"} />
                <Info
                  label="Completed"
                  value={scan.completed_at ? formatDate(scan.completed_at) : "—"}
                />
                <Info label="Findings" value={String(findings.length)} />
                <Info label="Recommendations" value={String(recommendations.length)} />
              </dl>
              {scan.status === "completed" && (
                <div className="mt-6 flex flex-wrap gap-2 border-t border-border pt-6">
                  <Button onClick={handleGenerateReport} loading={generating}>
                    Generate & download PDF
                  </Button>
                  <Button
                    variant="secondary"
                    loading={downloading === "json"}
                    disabled={!!downloading}
                    onClick={() => handleDownload("json")}
                  >
                    Export JSON
                  </Button>
                  <Button
                    variant="outline"
                    loading={downloading === "pdf"}
                    disabled={!!downloading}
                    onClick={() => handleDownload("pdf")}
                  >
                    Export PDF
                  </Button>
                </div>
              )}
            </Card>
          </div>
        </div>

        {scan.compliance_score && (
          <Card title="Score breakdown">
            <ScanScoreBreakdown score={scan.compliance_score} riskScore={scan.risk_score} />
          </Card>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Detected issues">
            {!findings.length ? (
              <div className="space-y-2">
                <p className="text-sm font-medium text-text-primary">No sensitive patterns found</p>
                <p className="text-sm text-text-muted">
                  The scanner did not detect credentials, API keys, contact information, or other
                  regulated patterns in the analyzed sample rows.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(findingsBySeverity).map(([severity, items]) => (
                  <div key={severity}>
                    <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
                      {severity} severity ({items.length})
                    </p>
                    <ul className="space-y-3">
                      {items.map((f) => (
                        <FindingCard key={f.id} finding={f} />
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Recommendations">
            {!recommendations.length ? (
              <p className="text-sm text-text-muted">
                No remediation steps required based on current findings.
              </p>
            ) : (
              <div className="space-y-6">
                {Object.entries(recsByPriority).map(([priority, items]) => (
                  <div key={priority}>
                    <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-text-muted">
                      {priority} priority ({items.length})
                    </p>
                    <ul className="space-y-4">
                      {items.map((r) => (
                        <li
                          key={r.id}
                          className="border-l-4 border-brand-500 bg-primary/10/30 py-2 pl-4 transition-colors hover:bg-primary/10/60"
                        >
                          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                            {r.action_type.replace(/_/g, " ")}
                            {r.column_name && (
                              <span className="ml-2 font-mono normal-case text-text-muted">
                                → {r.column_name}
                              </span>
                            )}
                          </p>
                          <p className="mt-1 font-semibold text-text-primary">{r.title}</p>
                          <p className="mt-1 text-sm text-text-muted">{r.description}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-text-muted">{label}</dt>
      <dd className="mt-1 font-medium text-text-primary">{value}</dd>
    </div>
  );
}

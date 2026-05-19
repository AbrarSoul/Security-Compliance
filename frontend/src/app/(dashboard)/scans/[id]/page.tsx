"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { ComplianceBadge, SeverityBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { RiskScoreGauge } from "@/components/scans/RiskScoreGauge";
import { StatCardSkeleton } from "@/components/ui/Skeleton";
import { filesApi, reportsApi, scansApi, triggerDownload, ApiError } from "@/lib/api";
import type { Scan, UploadedFile } from "@/lib/types";
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
        <Header title="Scan details" />
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
        <Header title="Scan details" />
        <div className="page-container">
          <Alert variant="error">{error || "Scan not found"}</Alert>
        </div>
      </>
    );
  }

  return (
    <>
      <Header
        title="Scan details"
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

        <div className="grid gap-6 lg:grid-cols-3">
          <Card title="Risk assessment">
            <div className="flex flex-col items-center py-4">
              <RiskScoreGauge score={scan.risk_score} />
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
            <Card title="Scan information">
              <dl className="grid gap-4 text-sm sm:grid-cols-2">
                <Info label="File" value={file?.original_name ?? scan.file_id} />
                <Info label="Status" value={statusLabel(scan.status)} />
                <Info label="Started" value={scan.started_at ? formatDate(scan.started_at) : "—"} />
                <Info
                  label="Completed"
                  value={scan.completed_at ? formatDate(scan.completed_at) : "—"}
                />
                <Info label="Findings" value={String(scan.findings?.length ?? 0)} />
                <Info label="Recommendations" value={String(scan.recommendations?.length ?? 0)} />
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

        <div className="grid gap-6 lg:grid-cols-2">
          <Card title="Detected issues">
            {!scan.findings?.length ? (
              <p className="text-sm text-text-muted">No issues detected.</p>
            ) : (
              <ul className="space-y-3">
                {scan.findings.map((f) => (
                  <li
                    key={f.id}
                    className="rounded-lg border border-border bg-background-tertiary/50 p-4 transition-colors hover:border-border hover:bg-surface"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold capitalize text-text-primary">
                        {f.finding_type.replace(/_/g, " ")}
                      </span>
                      <SeverityBadge severity={f.severity} />
                    </div>
                    {f.column_name && (
                      <p className="mt-1 text-sm text-text-muted">
                        Column: <span className="font-mono">{f.column_name}</span>
                      </p>
                    )}
                    <p className="mt-1 text-xs text-text-muted">
                      {f.sample_count} matches
                      {f.match_rate != null && ` · ${(f.match_rate * 100).toFixed(1)}% rate`}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <Card title="Recommendations">
            {!scan.recommendations?.length ? (
              <p className="text-sm text-text-muted">No recommendations.</p>
            ) : (
              <ul className="space-y-4">
                {scan.recommendations.map((r) => (
                  <li
                    key={r.id}
                    className="border-l-4 border-brand-500 bg-primary/10/30 py-2 pl-4 transition-colors hover:bg-primary/10/60"
                  >
                    <p className="text-xs font-semibold uppercase tracking-wide text-primary">
                      {r.priority} · {r.action_type.replace(/_/g, " ")}
                    </p>
                    <p className="mt-1 font-semibold text-text-primary">{r.title}</p>
                    <p className="mt-1 text-sm text-text-muted">{r.description}</p>
                  </li>
                ))}
              </ul>
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

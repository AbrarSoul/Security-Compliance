"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { ComplianceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { EmptyState } from "@/components/ui/EmptyState";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { reportsApi, triggerDownload, ApiError } from "@/lib/api";
import type { Report } from "@/lib/types";
import { formatDate, riskColor } from "@/lib/utils";

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    reportsApi
      .list()
      .then((r) => setReports(r.items))
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  async function download(reportId: string, format: "json" | "pdf") {
    setDownloading(`${reportId}-${format}`);
    setError("");
    try {
      const blob = await reportsApi.download(reportId, format);
      triggerDownload(blob, `compliance-report-${reportId}.${format}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  }

  return (
    <>
      <Header
        title="Compliance reports"
        subtitle="Download executive summaries and detailed compliance exports"
      />
      <div className="page-container space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        <Card
          title="Generated reports"
          description="Reports are created from completed scans. Generate from a scan detail page."
        >
          {loading ? (
            <TableSkeleton rows={5} />
          ) : reports.length === 0 ? (
            <EmptyState
              title="No reports yet"
              description="Complete a scan and generate a report from its detail page."
              action={
                <Link href="/scans">
                  <Button variant="secondary">View scans</Button>
                </Link>
              }
            />
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Report ID</th>
                    <th>Scan</th>
                    <th>Risk</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Downloads</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => {
                    const summary = r.executive_summary ?? {};
                    return (
                      <tr key={r.id}>
                        <td className="font-mono text-xs text-text-muted">{r.id.slice(0, 8)}…</td>
                        <td>
                          <Link
                            href={`/scans/${r.scan_id}`}
                            className="font-medium text-text-accent hover:text-primary"
                          >
                            {r.scan_id.slice(0, 8)}…
                          </Link>
                        </td>
                        <td>
                          <span
                            className={`font-mono font-bold ${riskColor(summary.risk_score as number)}`}
                          >
                            {summary.risk_score ?? "—"}
                          </span>
                        </td>
                        <td>
                          <ComplianceBadge status={summary.compliance_status as string} />
                        </td>
                        <td className="text-text-muted">{formatDate(r.created_at)}</td>
                        <td>
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              loading={downloading === `${r.id}-json`}
                              disabled={!!downloading}
                              onClick={() => download(r.id, "json")}
                            >
                              JSON
                            </Button>
                            <Button
                              variant="secondary"
                              loading={downloading === `${r.id}-pdf`}
                              disabled={!!downloading}
                              onClick={() => download(r.id, "pdf")}
                            >
                              PDF
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

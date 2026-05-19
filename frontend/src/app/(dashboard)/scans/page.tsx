"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { ComplianceBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { filesApi, scansApi } from "@/lib/api";
import type { Scan, UploadedFile } from "@/lib/types";
import { formatDate, riskColor, statusLabel } from "@/lib/utils";

export default function ScansPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [fileMap, setFileMap] = useState<Record<string, UploadedFile>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([scansApi.list(), filesApi.list()])
      .then(([s, f]) => {
        setScans(s.items);
        const map: Record<string, UploadedFile> = {};
        f.items.forEach((file) => {
          map[file.id] = file;
        });
        setFileMap(map);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <Header
        title="Compliance scans"
        subtitle="Review scan history, risk scores, and compliance status"
      />
      <div className="page-container">
        <Card
          title="Scan history"
          description="Select a scan to view findings, recommendations, and export reports."
        >
          {loading ? (
            <TableSkeleton rows={6} />
          ) : scans.length === 0 ? (
            <EmptyState
              title="No scans yet"
              description="Upload a dataset and run a scan to assess compliance risk."
              action={
                <Link href="/files">
                  <Button>Go to files</Button>
                </Link>
              }
            />
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Risk</th>
                    <th>Compliance</th>
                    <th>Classification</th>
                    <th>Findings</th>
                    <th>Date</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {scans.map((scan) => (
                    <tr key={scan.id}>
                      <td className="max-w-[200px] truncate font-medium text-text-primary">
                        {fileMap[scan.file_id]?.original_name ?? `${scan.file_id.slice(0, 8)}…`}
                      </td>
                      <td>
                        <span className="text-text-muted">{statusLabel(scan.status)}</span>
                      </td>
                      <td>
                        <span className={`font-mono font-bold ${riskColor(scan.risk_score)}`}>
                          {scan.risk_score ?? "—"}
                        </span>
                      </td>
                      <td>
                        <ComplianceBadge status={scan.compliance_status} />
                      </td>
                      <td className="capitalize text-text-muted">{scan.classification ?? "—"}</td>
                      <td className="font-mono text-text-muted">{scan.findings_count ?? 0}</td>
                      <td className="text-text-muted">{formatDate(scan.created_at)}</td>
                      <td>
                        <Link href={`/scans/${scan.id}`}>
                          <Button variant="outline" className="text-xs">
                            Details
                          </Button>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    </>
  );
}

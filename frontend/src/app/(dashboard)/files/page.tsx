"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/layout/Header";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { EmptyState } from "@/components/ui/EmptyState";
import { IconUpload } from "@/components/ui/icons";
import { TableSkeleton } from "@/components/ui/Skeleton";
import { filesApi, scansApi, ApiError } from "@/lib/api";
import {
  ALLOWED_DATASET_ACCEPT,
  ALLOWED_DATASET_LABEL,
} from "@/lib/allowedDatasetFormats";
import type { UploadedFile } from "@/lib/types";
import { formatBytes, formatDate } from "@/lib/utils";
export default function FilesPage() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    filesApi
      .list()
      .then((res) => setFiles(res.items))
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function uploadFile(file: File) {
    setError("");
    setMessage("");
    setUploading(true);
    try {
      await filesApi.upload(file);
      setMessage(`Uploaded ${file.name}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadFile(file);
    e.target.value = "";
  }

  async function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) await uploadFile(file);
  }

  async function handleScan(fileId: string) {
    setScanningId(fileId);
    setError("");
    try {
      const scan = await scansApi.create(fileId);
      setMessage("Scan completed");
      window.location.href = `/scans/${scan.id}`;
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Scan failed");
    } finally {
      setScanningId(null);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this file?")) return;
    try {
      await filesApi.delete(id);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Delete failed");
    }
  }

  return (
    <>
      <Header
        title="Uploaded files"
        subtitle="Manage datasets and trigger compliance scans"
      />
      <div className="page-container space-y-6">
        <Card
          title="Upload dataset"
          description={`${ALLOWED_DATASET_LABEL} — max 50 MB. Metadata is extracted on upload.`}
        >
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 transition-all duration-200 ${
              dragOver
                ? "border-brand-400 bg-primary/10"
                : "border-border bg-background-tertiary/50 hover:border-border-accent hover:bg-primary/10"
            }`}
          >
            <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/15 text-text-accent">
              <IconUpload />
            </div>
            <p className="text-sm font-medium text-text-secondary">
              Drag and drop a file, or choose from your computer
            </p>
            <p className="mt-1 text-xs text-text-muted">{ALLOWED_DATASET_LABEL}</p>
            <label className="mt-4 inline-block cursor-pointer">
              <input
                type="file"
                accept={ALLOWED_DATASET_ACCEPT}
                className="hidden"
                onChange={handleUpload}
                disabled={uploading}
              />
              <span className="pointer-events-none inline-flex">
                <Button type="button" loading={uploading}>
                  Choose file
                </Button>
              </span>
            </label>
          </div>
        </Card>

        {error && <Alert variant="error">{error}</Alert>}
        {message && <Alert variant="success">{message}</Alert>}

        <Card title="Your files">
          {loading ? (
            <TableSkeleton rows={4} />
          ) : files.length === 0 ? (
            <EmptyState
              title="No files uploaded"
              description="Upload a dataset to begin compliance scanning."
            />
          ) : (
            <div className="overflow-x-auto -mx-6 px-6">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Size</th>
                    <th>Rows</th>
                    <th>Columns</th>
                    <th>Uploaded</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((f) => (
                    <tr key={f.id}>
                      <td className="font-medium text-text-primary">{f.original_name}</td>
                      <td>
                        <span className="rounded bg-surface-elevated px-1.5 py-0.5 font-mono text-xs uppercase text-text-muted">
                          {f.file_type}
                        </span>
                      </td>
                      <td className="font-mono text-xs">{formatBytes(f.size_bytes)}</td>
                      <td className="font-mono text-xs">{f.metadata?.row_count ?? "—"}</td>
                      <td className="font-mono text-xs">{f.metadata?.column_count ?? "—"}</td>
                      <td className="text-text-muted">{formatDate(f.created_at)}</td>
                      <td>
                        <div className="flex gap-2">
                          <Button
                            variant="secondary"
                            loading={scanningId === f.id}
                            disabled={!!scanningId}
                            onClick={() => handleScan(f.id)}
                          >
                            Scan
                          </Button>
                          <Button variant="ghost" onClick={() => handleDelete(f.id)}>
                            Delete
                          </Button>
                        </div>
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

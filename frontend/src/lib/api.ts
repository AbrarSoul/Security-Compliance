import { getRefreshToken } from "./auth";
import { request } from "./api-core";
import type {
  Report,
  Scan,
  TokenResponse,
  UploadedFile,
  User,
  UserMe,
} from "./types";

export { ApiError, API_BASE } from "./api-core";
export * from "./api/sprint2";
export { analyticsApi } from "./api/analytics";
export { gapsApi } from "./api/gaps";
export { threatsApi } from "./api/threats";
export { gairaApi } from "./api/gaira";

// Auth
export const authApi = {
  signup: (body: { email: string; password: string; full_name?: string }) =>
    request<TokenResponse>("/auth/signup", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { email: string; password: string }) =>
    request<TokenResponse>("/auth/login", { method: "POST", body: JSON.stringify(body) }),

  me: () => request<UserMe>("/auth/me"),

  logout: () =>
    request<void>("/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: getRefreshToken() }),
    }),
};

// Files
export const filesApi = {
  list: () => request<{ items: UploadedFile[]; total: number }>("/files"),

  get: (id: string) => request<UploadedFile>(`/files/${id}`),

  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ file: UploadedFile; message: string }>("/files/upload", {
      method: "POST",
      body: form,
    });
  },

  delete: (id: string) => request<void>(`/files/${id}`, { method: "DELETE" }),
};

// Scans
export const scansApi = {
  list: () => request<{ items: Scan[]; total: number }>("/scans"),

  get: (id: string) => request<Scan>(`/scans/${id}`),

  create: (fileId: string) =>
    request<Scan>("/scans", {
      method: "POST",
      body: JSON.stringify({ file_id: fileId }),
    }),
};

// Reports
export const reportsApi = {
  list: () => request<{ items: Report[]; total: number }>("/reports"),

  get: (id: string) => request<Report & { summary?: Record<string, unknown> }>(`/reports/${id}`),

  generate: (scanId: string) =>
    request<{ report: Report; message: string }>("/reports", {
      method: "POST",
      body: JSON.stringify({ scan_id: scanId }),
    }),

  download: async (id: string, format: "json" | "pdf"): Promise<Blob> => {
    const { getAccessToken } = await import("./auth");
    const { API_BASE } = await import("./api-core");
    const token = getAccessToken();
    const res = await fetch(`${API_BASE}/reports/${id}/export?format=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      const { ApiError } = await import("./api-core");
      const text = await res.text();
      throw new ApiError(text, res.status);
    }
    return res.blob();
  },
};

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

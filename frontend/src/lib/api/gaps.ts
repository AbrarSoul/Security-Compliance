import { request } from "@/lib/api-core";
import type { ComplianceGap, GapAnalysisRun, GapDashboard } from "@/lib/types/gaps";

export const gapsApi = {
  dashboard() {
    return request<GapDashboard>("/gaps/dashboard");
  },

  list(params?: { severity?: string; gap_type?: string; status?: string }) {
    const p = new URLSearchParams();
    if (params?.severity) p.set("severity", params.severity);
    if (params?.gap_type) p.set("gap_type", params.gap_type);
    if (params?.status) p.set("status", params.status);
    const q = p.toString();
    return request<{
      items: ComplianceGap[];
      total: number;
      posture_score: number | null;
    }>(`/gaps${q ? `?${q}` : ""}`);
  },

  history(params?: { severity?: string; gap_type?: string }) {
    const p = new URLSearchParams();
    if (params?.severity) p.set("severity", params.severity);
    if (params?.gap_type) p.set("gap_type", params.gap_type);
    const q = p.toString();
    return request<{ items: ComplianceGap[]; total: number }>(`/gaps/history${q ? `?${q}` : ""}`);
  },

  runs() {
    return request<{ items: GapAnalysisRun[]; total: number }>("/gaps/runs");
  },

  analyze() {
    return request<GapAnalysisRun & { gaps: ComplianceGap[]; posture_score?: number }>(
      "/gaps/analyze",
      { method: "POST" }
    );
  },

  acknowledge(gapId: string) {
    return request<ComplianceGap>(`/gaps/${gapId}/acknowledge`, { method: "POST" });
  },

  resolve(gapId: string) {
    return request<ComplianceGap>(`/gaps/${gapId}/resolve`, { method: "POST" });
  },
};

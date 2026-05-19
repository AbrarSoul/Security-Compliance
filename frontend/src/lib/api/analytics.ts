import { request } from "@/lib/api-core";
import type { AnalyticsDashboard, AnalyticsFilters, AnalyticsSummary } from "@/lib/types/analytics";

function queryParams(filters: Partial<AnalyticsFilters> & { days?: number }): string {
  const p = new URLSearchParams();
  if (filters.days != null) p.set("days", String(filters.days));
  if (filters.severity) p.set("severity", filters.severity);
  if (filters.granularity) p.set("granularity", filters.granularity);
  const q = p.toString();
  return q ? `?${q}` : "";
}

export const analyticsApi = {
  dashboard(filters: Partial<AnalyticsFilters> = {}) {
    return request<AnalyticsDashboard>(`/analytics/dashboard${queryParams(filters)}`);
  },

  summary(filters: Partial<AnalyticsFilters> = {}) {
    return request<AnalyticsSummary>(`/analytics/summary${queryParams(filters)}`);
  },

  realtimeViolations(filters: Partial<AnalyticsFilters> = {}) {
    return request<{ items: AnalyticsDashboard["realtime_violations"]; total: number }>(
      `/analytics/violations/realtime${queryParams({ ...filters, days: filters.days ?? 7 })}`
    );
  },
};

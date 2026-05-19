/** Shared Recharts colors — single lime accent */

const LIME = "#a3e635";

export const CHART_COLORS = [LIME, LIME, LIME, LIME, LIME, LIME, LIME];

export const CHART_GRID = "#374151";
export const CHART_AXIS = "#94a3b8";

export function formatBucketLabel(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

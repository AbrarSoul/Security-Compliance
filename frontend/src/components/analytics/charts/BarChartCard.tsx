"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import type { LabelCount } from "@/lib/types/analytics";
import { CHART_AXIS, CHART_COLORS, CHART_GRID } from "./chartTheme";

type Props = {
  title: string;
  subtitle?: string;
  data: LabelCount[];
  height?: number;
};

export function BarChartCard({ title, subtitle, data, height = 260 }: Props) {
  const chartData = data.map((d) => ({ name: d.label, count: d.count }));

  return (
    <Card className="p-5">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        {subtitle ? <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p> : null}
      </div>
      {chartData.length === 0 ? (
        <div
          className="flex items-center justify-center rounded-lg border border-dashed border-border text-sm text-text-muted"
          style={{ height }}
        >
          No data for selected range
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
            <XAxis dataKey="name" tick={{ fill: CHART_AXIS, fontSize: 11 }} />
            <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} allowDecimals={false} />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: `1px solid ${CHART_GRID}`,
                background: "#1e293b",
                color: "#e2e8f0",
              }}
            />
            <Bar dataKey="count" fill={CHART_COLORS[0]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { Card } from "@/components/ui/Card";
import type { LabelCount } from "@/lib/types/analytics";
import { CHART_COLORS, CHART_GRID } from "./chartTheme";

type Props = {
  title: string;
  subtitle?: string;
  data: LabelCount[];
  height?: number;
};

export function PieChartCard({ title, subtitle, data, height = 260 }: Props) {
  const chartData = data.map((d) => ({ name: d.label, value: d.count }));

  return (
    <Card className="p-5">
      <ChartHeaderBlock title={title} subtitle={subtitle} />
      {chartData.length === 0 ? (
        <div
          className="flex items-center justify-center rounded-lg border border-dashed border-border text-sm text-text-muted"
          style={{ height }}
        >
          No data for selected range
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={90}
              label={({ name, percent }) =>
                `${name} ${(percent * 100).toFixed(0)}%`
              }
            >
              {chartData.map((_, i) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: `1px solid ${CHART_GRID}`,
                background: "#1e293b",
                color: "#e2e8f0",
              }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

function ChartHeaderBlock({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      {subtitle ? <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p> : null}
    </div>
  );
}

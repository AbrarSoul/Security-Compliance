"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { CHART_AXIS, CHART_COLORS, CHART_GRID, formatBucketLabel } from "./chartTheme";

export type LineChartPoint = { bucket: string; value: number };

type Props = {
  title: string;
  subtitle?: string;
  data: LineChartPoint[];
  height?: number;
};

function ChartHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      {subtitle ? <p className="mt-0.5 text-xs text-text-muted">{subtitle}</p> : null}
    </div>
  );
}

function EmptyState({ height }: { height: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-lg border border-dashed border-border text-sm text-text-muted"
      style={{ height }}
    >
      No data for selected range
    </div>
  );
}

export function LineChartCard({ title, subtitle, data, height = 260 }: Props) {
  const chartData = data.map((p) => ({
    ...p,
    label: formatBucketLabel(p.bucket),
  }));

  return (
    <Card className="p-5">
      <ChartHeader title={title} subtitle={subtitle} />
      {chartData.length === 0 ? (
        <EmptyState height={height} />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
            <XAxis dataKey="label" tick={{ fill: CHART_AXIS, fontSize: 11 }} />
            <YAxis tick={{ fill: CHART_AXIS, fontSize: 11 }} />
            <Tooltip
              contentStyle={{
                borderRadius: 8,
                border: `1px solid ${CHART_GRID}`,
                background: "#1e293b",
                color: "#e2e8f0",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={CHART_COLORS[0]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}

export function CountLineChartCard({
  title,
  subtitle,
  data,
  height = 260,
}: {
  title: string;
  subtitle?: string;
  data: { bucket: string; count: number }[];
  height?: number;
}) {
  const mapped = data.map((p) => ({ bucket: p.bucket, value: p.count }));
  return <LineChartCard title={title} subtitle={subtitle} data={mapped} height={height} />;
}

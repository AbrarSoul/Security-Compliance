"use client";

import { FormField } from "@/components/forms/FormField";
import { Select } from "@/components/forms/Select";
import type { AnalyticsFilters } from "@/lib/types/analytics";

type Props = {
  filters: AnalyticsFilters;
  onChange: (next: AnalyticsFilters) => void;
};

export function AnalyticsFiltersBar({ filters, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border border-border bg-surface p-4 shadow-card">
      <FormField label="Date range">
        <Select
          value={String(filters.days)}
          onChange={(e) => onChange({ ...filters, days: Number(e.target.value) })}
        >
          <option value="7">Last 7 days</option>
          <option value="14">Last 14 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </Select>
      </FormField>
      <FormField label="Severity">
        <Select
          value={filters.severity}
          onChange={(e) => onChange({ ...filters, severity: e.target.value })}
        >
          <option value="">All severities</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </Select>
      </FormField>
      <FormField label="Granularity">
        <Select
          value={filters.granularity}
          onChange={(e) =>
            onChange({
              ...filters,
              granularity: e.target.value as AnalyticsFilters["granularity"],
            })
          }
        >
          <option value="hour">Hourly</option>
          <option value="day">Daily</option>
          <option value="week">Weekly</option>
        </Select>
      </FormField>
    </div>
  );
}

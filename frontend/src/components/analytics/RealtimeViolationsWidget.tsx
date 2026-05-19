"use client";

import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { RealtimeViolation } from "@/lib/types/analytics";
import { formatDate, severityVariant } from "@/lib/utils";

type Props = {
  items: RealtimeViolation[];
  refreshing?: boolean;
};

export function RealtimeViolationsWidget({ items, refreshing }: Props) {
  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">Real-time violations</h3>
          <p className="mt-0.5 text-xs text-text-muted">Latest compliance events</p>
        </div>
        {refreshing ? (
          <span className="flex items-center gap-1.5 text-xs text-text-accent">
            <span className="h-2 w-2 animate-pulse rounded-full bg-primary/100" />
            Updating
          </span>
        ) : (
          <span className="text-xs text-text-muted">Live</span>
        )}
      </div>
      {items.length === 0 ? (
        <p className="py-8 text-center text-sm text-text-muted">No violations in range</p>
      ) : (
        <ul className="max-h-80 space-y-2 overflow-y-auto">
          {items.map((v) => (
            <li
              key={v.id}
              className="rounded-lg border border-border px-3 py-2.5 text-sm transition hover:bg-background-tertiary"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-medium text-text-secondary">{v.event_type}</span>
                <Badge variant={severityVariant(v.severity)}>{v.severity}</Badge>
              </div>
              <p className="mt-1 text-xs text-text-muted">{formatDate(v.occurred_at)}</p>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

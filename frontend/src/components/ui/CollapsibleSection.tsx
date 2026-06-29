"use client";

import { useState, type ReactNode } from "react";
import { Card } from "@/components/ui/Card";

type CollapsibleSectionProps = {
  title: string;
  subtitle?: string;
  meta?: string;
  defaultOpen?: boolean;
  children: ReactNode;
};

export function CollapsibleSection({
  title,
  subtitle,
  meta,
  defaultOpen = false,
  children,
}: CollapsibleSectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <Card className="overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-start justify-between gap-4 border-b border-border px-5 py-4 text-left transition-colors hover:bg-background-secondary/40"
      >
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
          {subtitle && <p className="mt-1 text-sm text-text-muted">{subtitle}</p>}
        </div>
        <span className="shrink-0 text-sm font-medium text-primary">
          {open ? "Hide" : "Show"}
          {meta ? ` · ${meta}` : ""}
        </span>
      </button>
      {open ? children : null}
    </Card>
  );
}

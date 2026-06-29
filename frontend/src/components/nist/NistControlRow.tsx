"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { controlDisplayInfo, controlReason, NIST_FUNCTION_INFO, suggestAction } from "@/lib/nistAiRmfInsights";
import type { NistControlStatusItem } from "@/lib/types/nistAiRmf";

export function NistControlRow({ control }: { control: NistControlStatusItem }) {
  const display = controlDisplayInfo(control);
  const functionInfo = NIST_FUNCTION_INFO[control.function];
  const reason = controlReason(control);
  const action = suggestAction(control);

  return (
    <li className="px-4 py-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-xs text-primary">{control.id}</span>
            {functionInfo && (
              <span className="text-[10px] uppercase tracking-wide text-text-muted">
                {functionInfo.title}
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-text-primary">{control.text}</p>

          <div className="mt-3 rounded-md border border-border/60 bg-background-secondary/30 px-3 py-2">
            <p className="text-xs text-text-secondary">
              <span className="font-semibold text-text-primary">Result: </span>
              {display.description}
            </p>
            <p className="mt-1 text-xs text-text-muted">
              <span className="font-semibold text-text-secondary">Evidence: </span>
              {reason}
            </p>
          </div>

          {control.notes && (
            <p className="mt-2 text-xs text-text-muted">
              <span className="font-semibold text-text-secondary">Note: </span>
              {control.notes}
            </p>
          )}

          {action && (
            <Link
              href={action.href}
              className="mt-2 inline-block text-xs font-medium text-primary hover:underline"
            >
              {action.label} →
            </Link>
          )}
        </div>

        <div className="flex shrink-0 flex-col items-end gap-1">
          <Badge variant={display.badgeVariant ?? "neutral"}>{display.label}</Badge>
          {control.coverage !== "none" && control.evidence_type && (
            <span className="text-[10px] text-text-muted">
              {control.evidence_type === "automated" ? "Auto-checked" : "Manual / hybrid"}
            </span>
          )}
        </div>
      </div>
    </li>
  );
}

"use client";

import { useEffect, useState } from "react";
import { riskColor } from "@/lib/utils";

export function RiskScoreGauge({ score }: { score: number | null | undefined }) {
  const value = score ?? 0;
  const pct = Math.min(100, Math.max(0, value));
  const color =
    value <= 30 ? "stroke-emerald-500" : value <= 60 ? "stroke-amber-500" : "stroke-red-500";

  const circumference = 2 * Math.PI * 45;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    const target = circumference - (pct / 100) * circumference;
    const timer = requestAnimationFrame(() => setOffset(target));
    return () => cancelAnimationFrame(timer);
  }, [pct, circumference]);

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-36 w-36">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="6"
            className="text-text-primary"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            className={`${color} transition-[stroke-dashoffset] duration-1000 ease-out`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-mono text-4xl font-bold tracking-tight ${riskColor(score)}`}>
            {score ?? "—"}
          </span>
          <span className="text-xs font-medium uppercase tracking-wider text-text-muted">/ 100</span>
        </div>
      </div>
      <p className="mt-3 text-sm font-medium text-text-muted">Risk score</p>
    </div>
  );
}

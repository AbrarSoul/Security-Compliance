"use client";

import { riskColor } from "@/lib/utils";

type StatCardProps = {
  label: string;
  value: string;
  subtext?: string;
  trend?: "up" | "down" | "neutral";
  valueClass?: string;
  icon?: React.ReactNode;
  delay?: number;
};

export function StatCard({
  label,
  value,
  subtext,
  valueClass,
  icon,
  delay = 0,
}: StatCardProps) {
  return (
    <div
      className="card-modern group relative overflow-hidden opacity-0 animate-fade-in-up"
      style={{ animationDelay: `${delay}ms`, animationFillMode: "forwards" }}
    >
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-full bg-primary/10 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-text-muted">{label}</p>
          <p
            className={`mt-2 font-mono text-3xl font-semibold tracking-tight ${valueClass ?? "text-text-primary"}`}
          >
            {value}
          </p>
          {subtext && <p className="mt-1 text-xs text-text-muted">{subtext}</p>}
        </div>
        {icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/15 text-primary transition-transform duration-300 group-hover:scale-105">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export function StatCardWithRisk({
  label,
  value,
  score,
  delay,
}: {
  label: string;
  value: string;
  score: number | null;
  delay?: number;
}) {
  return (
    <StatCard label={label} value={value} valueClass={riskColor(score)} delay={delay} />
  );
}

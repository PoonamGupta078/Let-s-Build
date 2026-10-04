import type { LucideIcon } from "lucide-react";
import type { Kpi } from "@/lib/types";

interface MetricCardProps {
  kpi: Kpi;
  icon: LucideIcon;
  /** Subtle accent hue for the icon well (violet | magenta | pink). */
  accent: "violet" | "magenta" | "pink";
  /** Positive delta renders in the low-risk green, else muted. */
  deltaTone?: "up" | "neutral";
}

const ACCENT_WELL: Record<MetricCardProps["accent"], string> = {
  violet: "bg-violet/12 text-violet border-violet/25",
  magenta: "bg-magenta/12 text-magenta border-magenta/25",
  pink: "bg-pink/12 text-pink border-pink/25",
};

/** KPI tile: label, main value, contextual change, restrained icon accent. */
export function MetricCard({
  kpi,
  icon: Icon,
  accent,
  deltaTone = "up",
}: MetricCardProps) {
  return (
    <article className="panel group flex items-start gap-4 p-4 transition-colors hover:border-line-strong">
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${ACCENT_WELL[accent]}`}
      >
        <Icon className="h-5 w-5" aria-hidden />
      </div>
      <div className="min-w-0">
        <p className="text-xs font-medium uppercase tracking-wider text-ink-3">
          {kpi.label}
        </p>
        <p className="mt-1 text-2xl font-semibold tabular-nums tracking-tight text-ink">
          {kpi.value}
        </p>
        <p
          className={`mt-1 text-xs ${
            deltaTone === "up" ? "text-risk-low" : "text-ink-3"
          }`}
        >
          {kpi.context}
        </p>
      </div>
    </article>
  );
}

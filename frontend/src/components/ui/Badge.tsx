import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type BadgeVariant =
  | "default"
  | "danger"
  | "warning"
  | "success"
  | "info"
  | "violet"
  | "magenta";

const STYLES: Record<BadgeVariant, string> = {
  default: "bg-surface-raised text-ink-2",
  danger: "bg-risk-critical/15 text-risk-critical border border-risk-critical/30",
  warning: "bg-risk-high/15 text-risk-high border border-risk-high/30",
  success: "bg-risk-low/15 text-risk-low border border-risk-low/30",
  info: "bg-status-investigating/15 text-status-investigating border border-status-investigating/30",
  violet: "bg-violet/15 text-violet border border-violet/30",
  magenta: "bg-magenta/15 text-magenta border border-magenta/30",
};

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

/** Small semantic chip (risk, status, counts). */
export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        STYLES[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}

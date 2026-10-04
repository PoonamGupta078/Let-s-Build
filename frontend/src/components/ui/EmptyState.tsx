import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  /** Optional action, e.g. a "Clear filters" button. */
  action?: ReactNode;
}

/**
 * Shown when a filtered list has no results — never a blank panel.
 * Reused by any list view (alert queue today, evidence later).
 */
export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="panel flex flex-col items-center gap-3 px-6 py-12 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-violet/25 bg-violet/10 text-violet">
        <Icon className="h-5 w-5" aria-hidden />
      </span>
      <div>
        <p className="text-sm font-medium text-ink">{title}</p>
        {description && <p className="mt-1 text-xs text-ink-2">{description}</p>}
      </div>
      {action}
    </div>
  );
}
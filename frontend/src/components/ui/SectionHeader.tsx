import type { ReactNode } from "react";

interface SectionHeaderProps {
  title: string;
  /** Optional muted subtitle under the title. */
  subtitle?: string;
  /** Right-aligned slot (e.g. a "View all" link). */
  action?: ReactNode;
}

/** Consistent heading for dashboard sections. */
export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
  return (
    <div className="mb-3 flex items-end justify-between gap-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-ink-2">
          {title}
        </h2>
        {subtitle && (
          <p className="mt-0.5 text-xs text-ink-3">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

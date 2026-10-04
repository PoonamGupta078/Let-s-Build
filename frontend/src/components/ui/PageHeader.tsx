import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  subtitle: string;
  /** Right-aligned slot (timestamps, badges, controls). */
  meta?: ReactNode;
}

/** Large page heading with contextual subtitle. */
export function PageHeader({ title, subtitle, meta }: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">
          {title}
        </h1>
        <p className="mt-1 text-sm text-ink-2">{subtitle}</p>
      </div>
      {meta && <div className="flex items-center gap-3">{meta}</div>}
    </div>
  );
}

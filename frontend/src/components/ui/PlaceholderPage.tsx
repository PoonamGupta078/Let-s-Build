import type { LucideIcon } from "lucide-react";
import { Construction } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";

interface PlaceholderPageProps {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  /** What this page will do once implemented. */
  description: string;
  /** Planned sections, shown as a list. */
  planned: string[];
}

/**
 * Scaffold for routes that exist in the shell but are implemented by a
 * later prompt. Honest about being a placeholder — no dead controls.
 */
export function PlaceholderPage({
  title,
  subtitle,
  icon: Icon,
  description,
  planned,
}: PlaceholderPageProps) {
  return (
    <>
      <PageHeader
        title={title}
        subtitle={subtitle}
        meta={
          <span className="rounded border border-line bg-glass px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-3">
            Coming later
          </span>
        }
      />

      <div className="panel flex max-w-2xl items-start gap-4 p-6">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-violet/25 bg-violet/10 text-violet">
          <Icon className="h-5 w-5" aria-hidden />
        </span>
        <div>
          <p className="text-sm font-medium text-ink">{description}</p>
          <p className="mt-4 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-3">
            <Construction className="h-3.5 w-3.5" aria-hidden />
            Planned sections
          </p>
          <ul className="mt-2 space-y-1.5">
            {planned.map((item) => (
              <li
                key={item}
                className="flex items-start gap-2 text-xs text-ink-2"
              >
                <span
                  className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-violet/60"
                  aria-hidden
                />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </>
  );
}

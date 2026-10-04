import { CircleCheck } from "lucide-react";
import type { TimelineEvent } from "@/lib/types";
import { relativeTime } from "@/lib/format";
import { SectionHeader } from "@/components/ui/SectionHeader";

/**
 * Chronological investigation timeline (prepares for the eventual audit
 * trail). Events are ordered oldest → newest.
 */
export function InvestigationTimeline({
  events,
}: {
  events: TimelineEvent[];
}) {
  return (
    <div className="panel p-5">
      <SectionHeader
        title="Investigation Timeline"
        subtitle="Chronological events for this investigation"
      />

      <ol className="relative space-y-5 before:absolute before:left-[12px] before:top-2 before:bottom-2 before:w-px before:bg-line">
        {events.map((event) => (
          <li key={event.id} className="relative flex gap-3">
            <span className="z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-violet/30 bg-surface text-violet">
              <CircleCheck className="h-3.5 w-3.5" aria-hidden />
            </span>
            <div className="min-w-0 pt-0.5">
              <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5">
                <p className="text-sm font-medium text-ink">{event.event}</p>
                <time
                  dateTime={event.timestamp}
                  className="shrink-0 text-[10px] tabular-nums text-ink-3"
                >
                  {relativeTime(event.timestamp)}
                </time>
              </div>
              <p className="mt-0.5 text-xs leading-relaxed text-ink-2">
                {event.description}
              </p>
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
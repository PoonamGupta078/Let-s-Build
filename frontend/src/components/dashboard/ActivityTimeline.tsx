import type { LucideIcon } from "lucide-react";
import {
  BellRing,
  CircleCheck,
  FileCheck,
  FolderPlus,
  Gavel,
  Route,
} from "lucide-react";
import type { ActivityEvent, ActivityKind } from "@/lib/types";
import { relativeTime } from "@/lib/format";

const KIND_STYLE: Record<
  ActivityKind,
  { icon: LucideIcon; tint: string }
> = {
  alert_created: { icon: BellRing, tint: "text-risk-high border-risk-high/30 bg-risk-high/10" },
  case_opened: { icon: FolderPlus, tint: "text-violet border-violet/30 bg-violet/10" },
  trace_completed: { icon: Route, tint: "text-magenta border-magenta/30 bg-magenta/10" },
  evidence_generated: { icon: FileCheck, tint: "text-risk-low border-risk-low/30 bg-risk-low/10" },
  plan_updated: { icon: CircleCheck, tint: "text-status-investigating border-status-investigating/30 bg-status-investigating/10" },
  decision_pending: { icon: Gavel, tint: "text-pink border-pink/30 bg-pink/10" },
};

/**
 * Recent investigation activity feed — visually walks the product flow:
 * alert → case → trace → evidence → plan → human decision.
 */
export function ActivityTimeline({ events }: { events: ActivityEvent[] }) {
  return (
    <div className="panel p-4">
      <ol className="relative space-y-5 before:absolute before:left-[15px] before:top-2 before:bottom-2 before:w-px before:bg-line">
        {events.map((event) => {
          const style = KIND_STYLE[event.kind];
          const Icon = style.icon;
          return (
            <li key={event.id} className="relative flex gap-3">
              <span
                className={`z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border backdrop-blur-sm ${style.tint}`}
              >
                <Icon className="h-4 w-4" aria-hidden />
              </span>
              <div className="min-w-0 pt-0.5">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5">
                  <p className="text-sm font-medium text-ink">{event.title}</p>
                  <time
                    dateTime={event.timestamp}
                    className="shrink-0 text-[10px] text-ink-3"
                  >
                    {relativeTime(event.timestamp)}
                  </time>
                </div>
                <p className="mt-0.5 text-xs leading-relaxed text-ink-2">
                  {event.detail}
                </p>
                <p className="mt-1 text-[10px] uppercase tracking-wider text-ink-3">
                  {event.actor}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

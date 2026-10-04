import { ArrowDown, Info } from "lucide-react";
import type { FundFlowStage } from "@/lib/types";
import { formatINRCompact } from "@/lib/format";

/**
 * Tainted → traced → interceptable funnel. A visual placeholder for the
 * future TRACE/CUT analytics; no taint algorithm runs here.
 */
export function FundFlowOverview({ stages }: { stages: FundFlowStage[] }) {
  const baseline = stages[0]?.amount ?? 0;

  return (
    <div className="panel p-4">
      <ol className="space-y-1">
        {stages.map((stage, i) => {
          const share =
            baseline > 0 ? Math.round((stage.amount / baseline) * 100) : 0;
          return (
            <li key={stage.label}>
              <div className="flex items-baseline justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-ink">{stage.label}</p>
                  <p className="mt-0.5 text-xs text-ink-3">{stage.note}</p>
                </div>
                <p className="shrink-0 text-lg font-semibold tabular-nums tracking-tight text-ink">
                  {formatINRCompact(stage.amount)}
                </p>
              </div>

              {i < stages.length - 1 && (
                <div className="my-2 flex items-center gap-2 pl-1">
                  <ArrowDown
                    className="h-4 w-4 text-magenta"
                    aria-hidden
                  />
                  <span className="text-[10px] font-medium uppercase tracking-wider text-ink-3">
                    {share}% of detected
                  </span>
                  <span
                    className="h-px flex-1 bg-line"
                    aria-hidden
                  />
                </div>
              )}
            </li>
          );
        })}
      </ol>

      <p className="mt-4 flex items-start gap-1.5 border-t border-line pt-3 text-[10px] leading-relaxed text-ink-3">
        <Info className="mt-px h-3 w-3 shrink-0" aria-hidden />
        Demo data — visual placeholder for TRACE/CUT analytics. No taint
        computation has run.
      </p>
    </div>
  );
}

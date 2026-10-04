import { ArrowDown, Info } from "lucide-react";
import type { Investigation } from "@/lib/types";
import { formatINR } from "@/lib/format";
import { SectionHeader } from "@/components/ui/SectionHeader";

/**
 * Money-flow summary (Source → Mule → Intermediary → Exit). Values are demo
 * mock hops — no taint propagation is computed (that arrives with TRACE).
 */
export function MoneyFlowSummary({
  investigation,
}: {
  investigation: Investigation;
}) {
  return (
    <div className="panel p-5">
      <SectionHeader
        title="Money Flow Summary"
        subtitle="Demo values — real taint propagation arrives with TRACE"
      />

      <ol className="space-y-1">
        {investigation.moneyFlow.map((stage, i) => (
          <li key={stage.label}>
            <div className="flex items-center justify-between gap-4 rounded-lg border border-line/60 bg-surface/40 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-ink">{stage.label}</p>
                <p className="mt-0.5 text-xs text-ink-3">{stage.note}</p>
              </div>
              <p className="shrink-0 text-sm font-semibold tabular-nums text-ink">
                {formatINR(stage.amount)}
              </p>
            </div>
            {i < investigation.moneyFlow.length - 1 && (
              <div className="flex items-center gap-2 py-1 pl-5">
                <ArrowDown className="h-3.5 w-3.5 text-magenta" aria-hidden />
              </div>
            )}
          </li>
        ))}
      </ol>

      <p className="mt-4 flex items-start gap-1.5 border-t border-line pt-3 text-[10px] leading-relaxed text-ink-3">
        <Info className="mt-px h-3 w-3 shrink-0" aria-hidden />
        Demo mock amounts — not computed by the TRACE engine yet.
      </p>
    </div>
  );
}
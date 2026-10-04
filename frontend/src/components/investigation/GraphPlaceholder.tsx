import { Network } from "lucide-react";
import { SectionHeader } from "@/components/ui/SectionHeader";

const LEGEND = [
  { label: "Source", tint: "bg-violet" },
  { label: "Mule", tint: "bg-magenta" },
  { label: "Intermediary", tint: "bg-pink" },
  { label: "Destination", tint: "bg-status-investigating" },
  { label: "Exit", tint: "bg-risk-critical" },
] as const;

/**
 * Polished placeholder for the transaction graph. The real Cytoscape
 * visualisation arrives with the next graph-specific prompt — no fake graph
 * is drawn here.
 */
export function GraphPlaceholder() {
  return (
    <div className="panel p-5">
      <SectionHeader
        title="Transaction Graph"
        subtitle="Connected fund-flow network for this investigation"
      />

      <div
        className="flex h-72 flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-line-strong/60 bg-surface/40"
        role="img"
        aria-label="Transaction graph placeholder"
      >
        <span className="flex h-12 w-12 items-center justify-center rounded-full border border-violet/30 bg-violet/10 text-violet">
          <Network className="h-6 w-6" aria-hidden />
        </span>
        <p className="max-w-sm px-6 text-center text-sm text-ink-2">
          Transaction graph will show the connected fund-flow network for this
          investigation.
        </p>
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-3">
          Coming in the next prompt
        </p>
      </div>

      {/* Legend */}
      <ul className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
        {LEGEND.map((item) => (
          <li key={item.label} className="flex items-center gap-1.5 text-xs text-ink-2">
            <span
              className={`h-2 w-2 rounded-full ${item.tint}`}
              aria-hidden
            />
            {item.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
import type { InvestigationStage } from "@/lib/types";

const STAGES: { key: InvestigationStage; label: string }[] = [
  { key: "SEE", label: "See" },
  { key: "TRACE", label: "Trace" },
  { key: "CUT", label: "Cut" },
  { key: "EVIDENCE", label: "Evidence" },
  { key: "CLINE", label: "Cline" },
  { key: "DECISION", label: "Decision" },
];

/**
 * Investigation workflow bar (SEE → … → DECISION). SEE is the active stage;
 * the rest are upcoming — no stage switching is wired yet.
 */
export function InvestigationWorkflow({ active }: { active: InvestigationStage }) {
  return (
    <nav
      aria-label="Investigation workflow"
      className="panel mb-6 flex flex-wrap items-center gap-x-1 gap-y-2 p-3"
    >
      {STAGES.map((stage, i) => {
        const isActive = stage.key === active;
        const isUpcoming = !isActive;
        return (
          <div key={stage.key} className="flex items-center gap-1">
            {i > 0 && (
              <span className="mx-1 text-ink-3" aria-hidden>
                →
              </span>
            )}
            <span
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold uppercase tracking-wider ${
                isActive
                  ? "border-violet/50 bg-violet/15 text-ink"
                  : isUpcoming
                    ? "border-line bg-glass text-ink-3"
                    : "border-line bg-glass text-ink-2"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isActive ? "bg-violet" : "bg-ink-3"
                }`}
                aria-hidden
              />
              {stage.label}
            </span>
          </div>
        );
      })}
    </nav>
  );
}
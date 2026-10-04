import { Check } from "lucide-react";
import type { InvestigationStage } from "@/lib/types";

const STAGES: { key: InvestigationStage; label: string; note: string }[] = [
  { key: "SEE", label: "See", note: "Current investigation" },
  { key: "TRACE", label: "Trace", note: "Available" },
  { key: "CUT", label: "Cut", note: "Not implemented" },
  { key: "EVIDENCE", label: "Evidence", note: "Existing UI" },
  { key: "CLINE", label: "Cline", note: "Existing UI" },
  { key: "DECISION", label: "Decision", note: "Existing UI" },
];

interface InvestigationWorkflowProps {
  active: InvestigationStage;
  /** TRACE run state; "running" makes the TRACE stage show as active. */
  traceRunning?: boolean;
}

/**
 * Investigation workflow bar (SEE → … → DECISION). SEE is current; TRACE is
 * the next available stage (highlighted while a trace is running). Later
 * stages are annotated but never falsely marked as completed.
 */
export function InvestigationWorkflow({
  active,
  traceRunning = false,
}: InvestigationWorkflowProps) {
  return (
    <nav
      aria-label="Investigation workflow"
      className="panel mb-6 flex flex-wrap items-center gap-x-1 gap-y-2 p-3"
    >
      {STAGES.map((stage, i) => {
        const isActive =
          stage.key === active || (stage.key === "TRACE" && traceRunning);
        const isCurrent = stage.key === active;
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
                  : "border-line bg-glass text-ink-3"
              }`}
            >
              {isCurrent && <Check className="h-3.5 w-3.5 text-violet" aria-hidden />}
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  isActive ? "bg-violet" : "bg-ink-3"
                }`}
                aria-hidden
              />
              {stage.label}
              <span className="ml-1 text-[9px] font-medium normal-case tracking-normal text-ink-3">
                {stage.note}
              </span>
            </span>
          </div>
        );
      })}
    </nav>
  );
}
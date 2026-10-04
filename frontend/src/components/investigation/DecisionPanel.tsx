import { Check, Gavel, ShieldAlert, X } from "lucide-react";

/**
 * Investigator decision area — the human-in-the-loop final step. APPROVE /
 * REJECT / ESCALATE are UI-only and never execute a freeze; a human decides.
 */
export function DecisionPanel() {
  return (
    <section aria-label="Investigator decision" className="panel border-risk-high/30 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-risk-high/30 bg-risk-high/10 text-risk-high">
            <Gavel className="h-4 w-4" aria-hidden />
          </span>
          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.14em] text-ink">
              Investigator Decision
              <span className="rounded border border-risk-high/40 bg-risk-high/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-risk-high">
                Human decision required
              </span>
            </h2>
            <p className="mt-0.5 text-xs text-ink-3">
              No action here executes a freeze — the investigator records the
              outcome of the recommended intervention.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled
            title="Decision recording will be connected to the backend later"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-risk-low/40 bg-risk-low/10 px-4 text-xs font-semibold text-risk-low opacity-60"
          >
            <Check className="h-3.5 w-3.5" aria-hidden />
            Approve
          </button>
          <button
            type="button"
            disabled
            title="Decision recording will be connected to the backend later"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-risk-critical/40 bg-risk-critical/10 px-4 text-xs font-semibold text-risk-critical opacity-60"
          >
            <X className="h-3.5 w-3.5" aria-hidden />
            Reject
          </button>
          <button
            type="button"
            disabled
            title="Decision recording will be connected to the backend later"
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-risk-high/40 bg-risk-high/10 px-4 text-xs font-semibold text-risk-high opacity-60"
          >
            <ShieldAlert className="h-3.5 w-3.5" aria-hidden />
            Escalate
          </button>
        </div>
      </div>

      <p className="mt-3 border-t border-line pt-3 text-[10px] leading-relaxed text-ink-3">
        Decision recording will be connected to the backend later. This
        console only recommends — a human investigator always decides.
      </p>
    </section>
  );
}
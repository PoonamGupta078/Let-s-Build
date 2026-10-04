import type { Metadata } from "next";
import { Clock, Info, Siren } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { AlertSummary } from "@/components/alerts/AlertSummary";
import { AlertQueue } from "@/components/alerts/AlertQueue";
import { CaseList } from "@/components/alerts/CaseList";
import { activeCases, alerts } from "@/lib/mock";
import { DEMO_NOW, formatDateTimeIST } from "@/lib/format";

export const metadata: Metadata = { title: "Alerts & Cases" };

/**
 * ALERT/CASE entry point of the investigator workflow:
 * New Alert → Review → Investigation → Decision.
 * Alerts are suspicious events awaiting review; cases are the
 * investigations opened from them.
 */
export default function AlertsPage() {
  return (
    <>
      <PageHeader
        title="Alerts & Cases"
        subtitle="Review suspicious activity and manage active investigations."
        meta={
          <>
            <span className="inline-flex items-center gap-1.5 rounded border border-line bg-glass px-2 py-1 text-xs text-ink-2">
              <Clock className="h-3.5 w-3.5 text-ink-3" aria-hidden />
              {formatDateTimeIST(DEMO_NOW)}
            </span>
            <span className="rounded border border-magenta/40 bg-magenta/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-magenta">
              Demo data
            </span>
          </>
        }
      />

      {/* Workflow legend: alert vs case, and where this page sits in it */}
      <div className="mb-6 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-line bg-glass px-4 py-2.5 text-xs text-ink-2">
        <span className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-ink">
          <Siren className="h-3.5 w-3.5 text-violet" aria-hidden />
          New Alert → Review → Investigation → Decision
        </span>
        <span className="flex items-center gap-1.5">
          <Info className="h-3.5 w-3.5 shrink-0 text-ink-3" aria-hidden />A{" "}
          <strong className="font-semibold text-ink">alert</strong> is a
          suspicious event requiring review.
        </span>
        <span>
          A <strong className="font-semibold text-ink">case</strong> is an
          investigation opened from suspicious activity.
        </span>
      </div>

      <AlertSummary alerts={alerts} />

      <section aria-label="Alert queue" className="mb-8">
        <SectionHeader
          title="Alert Queue"
          subtitle="System-generated alerts awaiting triage"
        />
        <AlertQueue alerts={alerts} />
      </section>

      <CaseList cases={activeCases} />
    </>
  );
}

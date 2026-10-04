import type { Metadata } from "next";
import { Clock, ShieldCheck, Siren, IndianRupee, Gavel } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { MetricCard } from "@/components/ui/MetricCard";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { AlertTable } from "@/components/dashboard/AlertTable";
import { InvestigationCard } from "@/components/dashboard/InvestigationCard";
import { FundFlowOverview } from "@/components/dashboard/FundFlowOverview";
import { ActivityTimeline } from "@/components/dashboard/ActivityTimeline";
import {
  activeCases,
  demoKpis,
  fundFlow,
  priorityAlerts,
  recentActivity,
} from "@/lib/mock";
import { DEMO_NOW, formatDateTimeIST } from "@/lib/format";

export const metadata: Metadata = {
  title: "Investigation Dashboard",
};

/** KPI icon/accent pairing (kept here, not in mock data). */
const KPI_VISUALS: Record<
  string,
  { icon: typeof Siren; accent: "violet" | "magenta" | "pink"; delta: "up" | "neutral" }
> = {
  "active-alerts": { icon: Siren, accent: "violet", delta: "up" },
  "high-risk-cases": { icon: ShieldCheck, accent: "pink", delta: "up" },
  "tainted-traced": { icon: IndianRupee, accent: "magenta", delta: "up" },
  "pending-decisions": { icon: Gavel, accent: "violet", delta: "neutral" },
};

export default function DashboardPage() {
  return (
    <>
      {/* A — Header */}
      <PageHeader
        title="Investigation Dashboard"
        subtitle="Monitor suspicious activity, active cases, and fund-flow investigations."
        meta={
          <>
            <span className="inline-flex items-center gap-1.5 rounded border border-line bg-glass px-2 py-1 text-xs text-ink-2">
              <Clock className="h-3.5 w-3.5 text-ink-3" aria-hidden />
              Last updated {formatDateTimeIST(DEMO_NOW)}
            </span>
            <span className="rounded border border-magenta/40 bg-magenta/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-magenta">
              Demo data
            </span>
          </>
        }
      />

      {/* B — KPI row */}
      <section aria-label="Summary metrics" className="mb-8">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {demoKpis.map((kpi) => {
            const visual = KPI_VISUALS[kpi.id];
            return (
              <MetricCard
                key={kpi.id}
                kpi={kpi}
                icon={visual.icon}
                accent={visual.accent}
                deltaTone={visual.delta}
              />
            );
          })}
        </div>
      </section>

      {/* C — Priority alerts */}
      <section aria-label="Priority alerts" className="mb-8">
        <SectionHeader
          title="Priority Alerts"
          subtitle="Highest-risk suspicious activity requiring review"
          action={
            <a
              href="/alerts"
              className="text-xs font-medium text-violet transition-colors hover:text-purple hover:underline"
            >
              View all alerts →
            </a>
          }
        />
        <AlertTable alerts={priorityAlerts} />
      </section>

      {/* D — Active investigations */}
      <section aria-label="Active investigations" className="mb-8">
        <SectionHeader
          title="Active Investigations"
          subtitle="Open cases — click a case to enter its workspace"
          action={
            <a
              href="/investigations"
              className="text-xs font-medium text-violet transition-colors hover:text-purple hover:underline"
            >
              View all cases →
            </a>
          }
        />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {activeCases.map((caseData) => (
            <InvestigationCard key={caseData.id} caseData={caseData} />
          ))}
        </div>
      </section>

      {/* E + F — Fund flow & activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <section aria-label="Fund flow overview" className="lg:col-span-2">
          <SectionHeader
            title="Fund Flow Overview"
            subtitle="Where tainted money is in the pipeline"
          />
          <FundFlowOverview stages={fundFlow} />
        </section>

        <section aria-label="Recent investigation activity" className="lg:col-span-3">
          <SectionHeader
            title="Recent Investigation Activity"
            subtitle="Alert → graph → trace → evidence → decision"
          />
          <ActivityTimeline events={recentActivity} />
        </section>
      </div>
    </>
  );
}

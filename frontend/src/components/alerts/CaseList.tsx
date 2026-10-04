import type { Case } from "@/lib/types";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { InvestigationCard } from "@/components/dashboard/InvestigationCard";

/**
 * "Active Cases" list for the Alerts page — cases are investigations opened
 * from suspicious activity (distinct from unreviewed alerts above). Cards
 * link to /investigations/[id].
 */
export function CaseList({ cases }: { cases: Case[] }) {
  return (
    <section aria-label="Active cases" className="mb-8">
      <SectionHeader
        title="Active Cases"
        subtitle="An investigation opened from suspicious activity — click a case to enter its workspace"
      />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cases.map((caseData) => (
          <InvestigationCard key={caseData.id} caseData={caseData} />
        ))}
      </div>
    </section>
  );
}
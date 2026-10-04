import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getInvestigation } from "@/lib/investigation";
import { InvestigationHeader } from "@/components/investigation/InvestigationHeader";
import { InvestigationWorkflow } from "@/components/investigation/InvestigationWorkflow";
import { InvestigationSummary } from "@/components/investigation/InvestigationSummary";
import { InvestigationFacts } from "@/components/investigation/InvestigationFacts";
import { GraphPlaceholder } from "@/components/investigation/GraphPlaceholder";
import { MoneyFlowSummary } from "@/components/investigation/MoneyFlowSummary";
import { DetectionFindings } from "@/components/investigation/DetectionFindings";
import { InvestigationTimeline } from "@/components/investigation/InvestigationTimeline";
import { EvidencePreview } from "@/components/investigation/EvidencePreview";
import { DecisionPanel } from "@/components/investigation/DecisionPanel";

export const metadata: Metadata = { title: "Investigation" };

interface PageProps {
  params: Promise<{ id: string }>;
}

/**
 * Investigation workspace — the central console where GRAPH / TRACE / CUT /
 * EVIDENCE / CLINE eventually come together. Currently the SEE stage: header,
 * workflow, graph placeholder, money-flow summary, findings, timeline and the
 * human decision area.
 */
export default async function InvestigationPage({ params }: PageProps) {
  const { id } = await params;
  const investigation = getInvestigation(id);
  if (!investigation) notFound();

  return (
    <div className="space-y-6">
      <InvestigationHeader investigation={investigation} />
      <InvestigationWorkflow active="SEE" />
      <InvestigationSummary investigation={investigation} />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Primary column: graph + money flow */}
        <div className="space-y-6 xl:col-span-2">
          <GraphPlaceholder />
          <MoneyFlowSummary investigation={investigation} />
        </div>

        {/* Right panel: facts + findings + evidence */}
        <div className="space-y-6">
          <InvestigationFacts investigation={investigation} />
          <DetectionFindings findings={investigation.findings} />
          <EvidencePreview summary={investigation.evidenceSummary} />
        </div>
      </div>

      <InvestigationTimeline events={investigation.timeline} />
      <DecisionPanel />
    </div>
  );
}
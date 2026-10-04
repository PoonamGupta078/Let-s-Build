import type { Metadata } from "next";
import { InvestigationWorkspace } from "@/components/investigation/InvestigationWorkspace";
import { PageHeader } from "@/components/ui/PageHeader";

export const metadata: Metadata = { title: "Investigation" };

interface PageProps {
  params: Promise<{ id: string }>;
}

/**
 * Investigation workspace — the transaction graph at the centre, with SEE
 * evidence, TRACE propagation and CUT recommendations connected to the real
 * API. All data is the synthetic demo case; a human always decides.
 */
export default async function InvestigationPage({ params }: PageProps) {
  const { id } = await params;
  return (
    <div className="space-y-6">
      <PageHeader
        title="Investigation Workspace"
        subtitle="SEE → TRACE → CUT over the synthetic demo case"
      />
      <InvestigationWorkspace initialAlertId={decodeURIComponent(id)} />
    </div>
  );
}

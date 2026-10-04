import type { Metadata } from "next";
import { FolderSearch } from "lucide-react";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = { title: "Investigations" };

export default function InvestigationsPage() {
  return (
    <PlaceholderPage
      title="Investigations"
      subtitle="Active fund-flow investigations and case workspaces."
      icon={FolderSearch}
      description="The investigation workspace where TRACE, CUT and the transaction graph come together."
      planned={[
        "Transaction graph view (Cytoscape.js) per case",
        "Taint trail (TRACE) with rupee-level propagation",
        "Hold recommendations (CUT) with impact estimates",
        "Investigator Copilot side panel",
      ]}
    />
  );
}

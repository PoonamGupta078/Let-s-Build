import type { Metadata } from "next";
import { Siren } from "lucide-react";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = { title: "Alerts & Cases" };

export default function AlertsPage() {
  return (
    <PlaceholderPage
      title="Alerts & Cases"
      subtitle="Review, triage and assign system-generated alerts."
      icon={Siren}
      description="The full alert queue and case management view."
      planned={[
        "Alert queue with risk-score sorting and pattern filters",
        "Alert detail: graph context, evidence indicators, txn citations",
        "Case creation, assignment and status transitions",
        "Bulk triage actions",
      ]}
    />
  );
}

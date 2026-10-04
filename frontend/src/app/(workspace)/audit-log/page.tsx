import type { Metadata } from "next";
import { ScrollText } from "lucide-react";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = { title: "Audit Log" };

export default function AuditLogPage() {
  return (
    <PlaceholderPage
      title="Audit Log"
      subtitle="Immutable trail of investigator and system actions."
      icon={ScrollText}
      description="Every decision, recommendation and access recorded for review."
      planned={[
        "Investigator decisions with timestamps and reasons",
        "System actions (alerts, traces, evidence generation)",
        "Filter by case, actor and action type",
        "Export for compliance review",
      ]}
    />
  );
}

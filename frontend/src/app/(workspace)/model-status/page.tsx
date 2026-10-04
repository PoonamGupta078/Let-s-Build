import type { Metadata } from "next";
import { Activity } from "lucide-react";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = { title: "Model Status" };

export default function ModelStatusPage() {
  return (
    <PlaceholderPage
      title="Model Status"
      subtitle="Detector health and fusion scoring status."
      icon={Activity}
      description="Operational view of the SEE-layer detectors and the fusion scorer."
      planned={[
        "Per-detector status (GraphSAGE, Node2Vec, Isolation Forest, rules)",
        "Fusion score distribution and thresholds",
        "Last scoring run timestamps",
        "Drift and degradation indicators",
      ]}
    />
  );
}

import type { Metadata } from "next";
import { Database } from "lucide-react";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = { title: "Data" };

export default function DataPage() {
  return (
    <PlaceholderPage
      title="Data"
      subtitle="Transaction feeds and dataset status."
      icon={Database}
      description="Ingestion status for the transaction feeds backing detection and tracing."
      planned={[
        "Loaded dataset summary and row counts",
        "Validation results (rejected rows, reasons)",
        "Ingestion timestamps and feed health",
        "Sample case dataset status",
      ]}
    />
  );
}

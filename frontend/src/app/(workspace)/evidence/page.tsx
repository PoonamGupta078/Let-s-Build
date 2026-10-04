import type { Metadata } from "next";
import { FileCheck } from "lucide-react";
import { PlaceholderPage } from "@/components/ui/PlaceholderPage";

export const metadata: Metadata = { title: "Evidence" };

export default function EvidencePage() {
  return (
    <PlaceholderPage
      title="Evidence"
      subtitle="Evidence packs and STR-style reports for filing."
      icon={FileCheck}
      description="Generated evidence packages with hashes and linked transaction IDs."
      planned={[
        "STR-style report preview with narrative per txn_id",
        "SHA-256 hashes for JSON and PDF artefacts",
        "Download and export history",
        "Audit trail of evidence access",
      ]}
    />
  );
}

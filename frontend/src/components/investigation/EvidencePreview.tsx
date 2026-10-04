import Link from "next/link";
import { FileCheck, Link2, ScanSearch } from "lucide-react";
import type { EvidenceSummary } from "@/lib/types";
import { relativeTime } from "@/lib/format";
import { SectionHeader } from "@/components/ui/SectionHeader";

const STATUS_LABEL: Record<EvidenceSummary["status"], string> = {
  NOT_STARTED: "Not started",
  DRAFT: "Draft",
  READY: "Ready",
};

/**
 * Compact evidence preview. The full evidence pack / STR generation arrives
 * with a later prompt.
 */
export function EvidencePreview({
  summary,
}: {
  summary: EvidenceSummary;
}) {
  return (
    <div className="panel p-5">
      <SectionHeader
        title="Evidence Preview"
        subtitle="Evidence pack summary"
        action={
          <span className="rounded border border-line bg-glass px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-ink-2">
            {STATUS_LABEL[summary.status]}
          </span>
        }
      />

      <dl className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-line/60 bg-surface/40 p-3">
          <dt className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            <Link2 className="h-3 w-3" aria-hidden />
            Linked transactions
          </dt>
          <dd className="mt-1 text-lg font-semibold tabular-nums text-ink">
            {summary.linkedTransactions}
          </dd>
        </div>
        <div className="rounded-lg border border-line/60 bg-surface/40 p-3">
          <dt className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-3">
            <ScanSearch className="h-3 w-3" aria-hidden />
            Detector findings
          </dt>
          <dd className="mt-1 text-lg font-semibold tabular-nums text-ink">
            {summary.detectorFindings}
          </dd>
        </div>
      </dl>

      <div className="mt-3 flex items-center justify-between gap-3 border-t border-line pt-3 text-xs">
        <span className="text-ink-3">
          Last update{" "}
          <span className="tabular-nums text-ink-2">
            {relativeTime(summary.lastUpdated)}
          </span>
        </span>
        <Link
          href="/evidence"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-violet transition-colors hover:text-purple hover:underline"
        >
          <FileCheck className="h-3.5 w-3.5" aria-hidden />
          View evidence →
        </Link>
      </div>
    </div>
  );
}
import Link from "next/link";
import { ChevronRight, Users } from "lucide-react";
import type { Case } from "@/lib/types";
import { formatINRCompact, relativeTime } from "@/lib/format";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { StatusBadge } from "@/components/ui/StatusBadge";

/**
 * Active investigation card. Clicking opens the case — routed to the
 * investigations workspace (detail view arrives with a later prompt).
 */
export function InvestigationCard({ caseData }: { caseData: Case }) {
  return (
    <Link
      href="/investigations"
      className="panel group flex flex-col gap-3 p-4 transition-colors hover:border-line-strong"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="font-mono text-xs font-medium text-violet">
          {caseData.id}
        </span>
        <StatusBadge status={caseData.status} />
      </div>

      <p className="text-sm font-medium leading-snug text-ink transition-colors group-hover:text-white">
        {caseData.title}
      </p>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-ink-2">
        <RiskBadge score={caseData.riskScore} showLabel={false} />
        <span className="inline-flex items-center gap-1.5">
          <Users className="h-3.5 w-3.5 text-ink-3" aria-hidden />
          {caseData.accounts} accounts
        </span>
        <span className="font-medium tabular-nums text-ink">
          {formatINRCompact(caseData.taintedAmount)}
        </span>
      </div>

      <div className="mt-auto flex items-center justify-between border-t border-line pt-3 text-xs">
        <span className="text-ink-2">
          {caseData.investigator} ·{" "}
          <span className="text-ink-3">{relativeTime(caseData.lastActivity)}</span>
        </span>
        <span className="inline-flex items-center gap-1 font-medium text-violet opacity-0 transition-opacity group-hover:opacity-100">
          Open
          <ChevronRight className="h-3.5 w-3.5" aria-hidden />
        </span>
      </div>
    </Link>
  );
}

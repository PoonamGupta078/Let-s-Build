import type { Investigation } from "@/lib/types";
import { formatINR } from "@/lib/format";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { SectionHeader } from "@/components/ui/SectionHeader";

/** Field row for the compact summary panel. */
function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5">
      <dt className="text-xs uppercase tracking-wider text-ink-3">{label}</dt>
      <dd className="text-right font-mono text-xs text-ink-2">{value}</dd>
    </div>
  );
}

/**
 * Right-panel compact investigation summary (primary account, risk, pattern,
 * accounts involved, tainted amount).
 */
export function InvestigationFacts({
  investigation,
}: {
  investigation: Investigation;
}) {
  return (
    <div className="panel p-5">
      <SectionHeader title="Investigation Summary" />
      <dl className="divide-y divide-line/60">
        <Fact label="Primary account" value={investigation.primaryAccount} />
        <div className="flex items-baseline justify-between gap-4 py-1.5">
          <dt className="text-xs uppercase tracking-wider text-ink-3">
            Risk score
          </dt>
          <dd>
            <RiskBadge score={investigation.riskScore} />
          </dd>
        </div>
        <Fact label="Pattern" value={investigation.pattern} />
        <Fact label="Accounts involved" value={`${investigation.accountsInvolved}`} />
        <Fact label="Tainted amount" value={formatINR(investigation.taintedAmount)} />
      </dl>
    </div>
  );
}
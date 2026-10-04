import {
  ArrowLeftRight,
  IndianRupee,
  LogOut,
  ShieldAlert,
  Users,
} from "lucide-react";
import type { Investigation } from "@/lib/types";
import { formatINR } from "@/lib/format";
import { MetricCard } from "@/components/ui/MetricCard";
import { riskBand } from "@/components/ui/RiskBadge";

/**
 * Summary strip: risk score, tainted funds, accounts, transactions and
 * potential exits. Values come straight off the Investigation payload so the
 * same shape can later come from GET /api/case.
 */
export function InvestigationSummary({
  investigation,
}: {
  investigation: Investigation;
}) {
  const metrics = [
    {
      id: "risk",
      label: "Risk Score",
      value: `${investigation.riskScore}`,
      context: riskBand(investigation.riskScore),
      icon: ShieldAlert,
      accent: "pink" as const,
    },
    {
      id: "tainted",
      label: "Tainted Funds",
      value: formatINR(investigation.taintedAmount),
      context: "Estimated tainted ₹",
      icon: IndianRupee,
      accent: "magenta" as const,
    },
    {
      id: "accounts",
      label: "Accounts Involved",
      value: `${investigation.accountsInvolved}`,
      context: "In the network",
      icon: Users,
      accent: "violet" as const,
    },
    {
      id: "transactions",
      label: "Transactions",
      value: `${investigation.transactions}`,
      context: "Linked to the case",
      icon: ArrowLeftRight,
      accent: "violet" as const,
    },
    {
      id: "exits",
      label: "Potential Exits",
      value: `${investigation.potentialExits}`,
      context: "Cash-out / other-bank",
      icon: LogOut,
      accent: "magenta" as const,
    },
  ];

  return (
    <section aria-label="Investigation summary" className="mb-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        {metrics.map((m) => (
          <MetricCard
            key={m.id}
            kpi={{ id: m.id, label: m.label, value: m.value, context: m.context }}
            icon={m.icon}
            accent={m.accent}
            deltaTone="neutral"
          />
        ))}
      </div>
    </section>
  );
}
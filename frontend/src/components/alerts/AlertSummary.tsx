import type { LucideIcon } from "lucide-react";
import { Gavel, Search, ShieldCheck, Siren, BellRing } from "lucide-react";
import type { Alert, AlertStatus, Kpi } from "@/lib/types";
import { MetricCard } from "@/components/ui/MetricCard";
import { riskBand } from "@/components/ui/RiskBadge";

interface Metric {
  kpi: Kpi;
  icon: LucideIcon;
  accent: "violet" | "magenta" | "pink";
}

/**
 * Queue summary tiles — every number is derived from the centralised mock
 * alerts (never hand-written), so the tiles can never drift from the queue.
 */
export function AlertSummary({ alerts }: { alerts: Alert[] }) {
  const countStatus = (status: AlertStatus): number =>
    alerts.filter((alert) => alert.status === status).length;
  const highRisk = alerts.filter((alert) => {
    const band = riskBand(alert.riskScore);
    return band === "CRITICAL" || band === "HIGH";
  }).length;

  const metrics: Metric[] = [
    {
      kpi: {
        id: "total-alerts",
        label: "Total Alerts",
        value: String(alerts.length),
        context: "In the review queue",
      },
      icon: Siren,
      accent: "violet",
    },
    {
      kpi: {
        id: "high-risk",
        label: "High Risk",
        value: String(highRisk),
        context: "Fusion score 75+",
      },
      icon: ShieldCheck,
      accent: "pink",
    },
    {
      kpi: {
        id: "new-alerts",
        label: "New",
        value: String(countStatus("NEW")),
        context: "Awaiting first review",
      },
      icon: BellRing,
      accent: "magenta",
    },
    {
      kpi: {
        id: "investigating",
        label: "Investigating",
        value: String(countStatus("INVESTIGATING")),
        context: "Under active review",
      },
      icon: Search,
      accent: "violet",
    },
    {
      kpi: {
        id: "pending-decision",
        label: "Pending Decision",
        value: String(countStatus("ESCALATED")),
        context: "Escalated to a human",
      },
      icon: Gavel,
      accent: "pink",
    },
  ];

  return (
    <section aria-label="Queue summary" className="mb-8">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        {metrics.map(({ kpi, icon, accent }) => (
          <MetricCard
            key={kpi.id}
            kpi={kpi}
            icon={icon}
            accent={accent}
            deltaTone="neutral"
          />
        ))}
      </div>
    </section>
  );
}
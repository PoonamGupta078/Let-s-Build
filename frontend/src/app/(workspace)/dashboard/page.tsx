"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowLeftRight,
  DoorOpen,
  Siren,
  UserRound,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import type { GraphData, OverviewData, SeeAlert } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { MetricCard } from "@/components/ui/MetricCard";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { Loader, SkeletonCard } from "@/components/ui/Loader";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [alerts, setAlerts] = useState<SeeAlert[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.overview(), api.alerts(), api.graph()])
      .then(([o, a, g]) => {
        setOverview(o);
        setAlerts(a);
        setGraph(g);
      })
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="panel p-5 text-sm text-risk-critical">{error}</div>;

  if (!overview || !graph) {
    return (
      <div className="space-y-6">
        <PageHeader title="Dashboard" subtitle="Investigation overview" />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <Loader label="Loading dashboard…" />
      </div>
    );
  }

  const kpis = [
    { id: "accounts", label: "Accounts", value: String(overview.accounts), context: "in demo network", icon: Users, accent: "violet" as const },
    { id: "transactions", label: "Transactions", value: String(overview.transactions), context: "directed edges", icon: ArrowLeftRight, accent: "magenta" as const },
    { id: "alerts", label: "SEE Alerts", value: String(overview.alerts), context: "rapid pass-through", icon: Siren, accent: "pink" as const },
    { id: "exits", label: "Exits", value: String(overview.exits), context: "cash-out accounts", icon: DoorOpen, accent: "violet" as const },
    { id: "seeds", label: "Seed Accounts", value: String(overview.seed_accounts), context: "confirmed-bad source", icon: UserRound, accent: "magenta" as const },
    { id: "rules", label: "Rules Fired", value: String(Object.keys(overview.rule_distribution).length), context: "distinct SEE rules", icon: Activity, accent: "pink" as const },
  ];

  const sortedAlerts = [...alerts].sort((a, b) => b.score - a.score);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Synthetic demo case — SEE / TRACE / CUT connected to the live API"
        meta={<Badge variant="magenta">Demo</Badge>}
      />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {kpis.map((k) => (
          <MetricCard
            key={k.id}
            kpi={{ id: k.id, label: k.label, value: k.value, context: k.context }}
            icon={k.icon}
            accent={k.accent}
            deltaTone="neutral"
          />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="panel p-5 lg:col-span-2">
          <SectionHeader
            title="Fund-Flow Network"
            subtitle="Interactive preview of the demo graph"
            action={
              <Link href="/graph" className="text-xs font-medium text-violet hover:text-ink">
                Open Graph Explorer →
              </Link>
            }
          />
          <CytoscapeGraph data={graph} height={340} />
        </div>

        <div className="space-y-6">
          <div className="panel p-5">
            <SectionHeader title="Rule Distribution" subtitle="SEE rules fired" />
            <ul className="space-y-2">
              {Object.entries(overview.rule_distribution).map(([rule, count]) => (
                <li
                  key={rule}
                  className="flex items-center justify-between rounded-lg border border-line/60 bg-surface/40 px-3 py-2"
                >
                  <span className="font-mono text-xs text-ink">{rule}</span>
                  <Badge variant="violet">{count}</Badge>
                </li>
              ))}
            </ul>
          </div>

          <div className="panel p-5">
            <SectionHeader
              title="Recent Alerts"
              subtitle="Highest risk first"
              action={
                <Link href="/alerts" className="text-xs font-medium text-violet hover:text-ink">
                  View all →
                </Link>
              }
            />
            <ul className="space-y-2">
              {sortedAlerts.map((a) => (
                <li key={a.alert_id}>
                  <Link
                    href={`/investigations/${a.alert_id}`}
                    className="flex items-center justify-between rounded-lg border border-line/60 bg-surface/40 px-3 py-2 transition-colors hover:border-line-strong"
                  >
                    <div>
                      <p className="text-sm font-medium text-ink">{a.account}</p>
                      <p className="text-[11px] text-ink-3">{a.rule_name}</p>
                    </div>
                    <RiskBadge score={a.score} />
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <p className="text-center text-[11px] text-ink-3">
        Synthetic demo data from make_case(seed=42, background_rows=0). No ML
        metrics are shown here — the preliminary baseline experiments are
        documented in docs/ml_baseline.md.
      </p>
    </div>
  );
}


"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Search } from "lucide-react";
import { api } from "@/lib/api";
import type { SeeAlert } from "@/lib/types";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { Loader } from "@/components/ui/Loader";

type SortKey = "score" | "account" | "rule";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<SeeAlert[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [rule, setRule] = useState("ALL");
  const [sort, setSort] = useState<SortKey>("score");

  useEffect(() => {
    api.alerts().then(setAlerts).catch((e) => setError(String(e)));
  }, []);

  const rules = useMemo(
    () => Array.from(new Set((alerts ?? []).map((a) => a.rule_id))).sort(),
    [alerts],
  );

  const visible = useMemo(() => {
    let list = alerts ?? [];
    if (rule !== "ALL") list = list.filter((a) => a.rule_id === rule);
    const q = query.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (a) =>
          a.account.toLowerCase().includes(q) ||
          a.alert_id.toLowerCase().includes(q) ||
          a.rule_name.toLowerCase().includes(q),
      );
    }
    return [...list].sort((a, b) => {
      if (sort === "score") return b.score - a.score;
      if (sort === "account") return a.account.localeCompare(b.account);
      return a.rule_name.localeCompare(b.rule_name);
    });
  }, [alerts, query, rule, sort]);

  if (error) return <div className="panel p-5 text-sm text-risk-critical">{error}</div>;
  if (!alerts) return <Loader label="Loading alerts…" />;

  return (
    <>
      <PageHeader
        title="Alerts"
        subtitle="SEE suspicious-activity alerts — synthetic demo data"
        meta={<Badge variant="magenta">Demo</Badge>}
      />

      <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border border-line bg-surface/40 p-3">
        <label className="relative min-w-52 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-3" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search account, alert id or rule…"
            className="h-9 w-full rounded-md border border-line bg-glass pl-8 pr-3 text-xs text-ink placeholder:text-ink-3 outline-none focus:border-line-strong"
            aria-label="Search alerts"
          />
        </label>
        <select
          value={rule}
          onChange={(e) => setRule(e.target.value)}
          className="h-9 rounded-md border border-line bg-glass px-2 text-xs text-ink outline-none focus:border-line-strong"
          aria-label="Filter by rule"
        >
          <option value="ALL">Rule: All</option>
          {rules.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="h-9 rounded-md border border-line bg-glass px-2 text-xs text-ink outline-none focus:border-line-strong"
          aria-label="Sort alerts"
        >
          <option value="score">Sort: Risk</option>
          <option value="account">Sort: Account</option>
          <option value="rule">Sort: Rule</option>
        </select>
        <span className="ml-auto text-[11px] text-ink-3 tabular-nums">
          {visible.length} of {alerts.length}
        </span>
      </div>

      <div className="panel overflow-x-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead>
            <tr className="border-b border-line text-[10px] font-semibold uppercase tracking-wider text-ink-3">
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Rule</th>
              <th className="px-4 py-3">Account</th>
              <th className="px-4 py-3">Explanation</th>
              <th className="px-4 py-3">Evidence</th>
              <th className="px-4 py-3" aria-label="Action" />
            </tr>
          </thead>
          <tbody>
            {visible.map((a) => (
              <tr key={a.alert_id} className="border-b border-line/50 transition-colors hover:bg-surface-raised/60">
                <td className="px-4 py-3"><RiskBadge score={a.score} /></td>
                <td className="px-4 py-3">
                  <p className="font-medium text-ink">{a.rule_name}</p>
                  <p className="text-[10px] text-ink-3">{a.rule_id}</p>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-ink">{a.account}</td>
                <td className="max-w-sm px-4 py-3 text-xs leading-relaxed text-ink-2">{a.explanation}</td>
                <td className="px-4 py-3 font-mono text-[11px] text-ink-3">{a.evidence_txn_ids.join(", ")}</td>
                <td className="px-4 py-3 text-right">
                  <Link href={`/investigations/${a.alert_id}`} className="inline-flex items-center gap-1 text-xs font-medium text-violet hover:text-ink">
                    Investigate <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}


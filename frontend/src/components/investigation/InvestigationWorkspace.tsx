"use client";

/**
 * Investigation workspace backed by the real SEE / TRACE / CUT API.
 *
 * Fetches alerts, graph, trace, and cut together and renders them as one
 * connected view: selecting an alert highlights its evidence transactions in
 * the graph, TRACE paths show account-to-account estimated propagation, and
 * CUT shows advisory recommendations. All data is the synthetic demo case.
 */
import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { CutData, GraphData, SeeAlert, TraceData } from "@/lib/types";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Badge } from "@/components/ui/Badge";
import { RiskBadge } from "@/components/ui/RiskBadge";
import { Loader } from "@/components/ui/Loader";

interface InvestigationWorkspaceProps {
  initialAlertId?: string;
}

export function InvestigationWorkspace({ initialAlertId }: InvestigationWorkspaceProps) {
  const [alerts, setAlerts] = useState<SeeAlert[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [cut, setCut] = useState<CutData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.alerts(), api.graph(), api.trace(), api.cut()])
      .then(([a, g, t, c]) => {
        setAlerts(a);
        setGraph(g);
        setTrace(t);
        setCut(c);
        setSelectedAlertId((prev) => {
          if (prev) return prev;
          const match = a.find(
            (x) =>
              x.alert_id === initialAlertId || x.account === initialAlertId,
          );
          return match?.alert_id ?? a[0]?.alert_id ?? null;
        });
      })
      .catch((e) => setError(String(e)));
  }, [initialAlertId]);

  const traceTxnIds = useMemo(() => {
    const ids = new Set<string>();
    trace?.paths.forEach((p) => p.steps.forEach((s) => ids.add(s.txn_id)));
    return ids;
  }, [trace]);

  const highlightedTxnIds = useMemo(() => {
    const ids = new Set<string>(
      alerts.find((a) => a.alert_id === selectedAlertId)?.evidence_txn_ids ?? [],
    );
    traceTxnIds.forEach((id) => ids.add(id));
    return Array.from(ids);
  }, [alerts, selectedAlertId, traceTxnIds]);

  const selectedAlert = alerts.find((a) => a.alert_id === selectedAlertId);

  if (error) {
    return (
      <div className="panel p-5 text-sm text-risk-critical">{error}</div>
    );
  }

  if (!graph || !trace || !cut) {
    return <Loader label="Loading investigation…" />;
  }

  return (
    <div className="space-y-6">
      <div className="panel p-5">
        <SectionHeader
          title="SEE Alerts"
          subtitle="Select an alert to highlight its evidence transactions in the graph"
        />
        <ul className="flex flex-wrap gap-2">
          {alerts.map((alert) => (
            <li key={alert.alert_id}>
              <button
                type="button"
                onClick={() => setSelectedAlertId(alert.alert_id)}
                className={`rounded-lg border px-3 py-2 text-left text-xs transition-colors ${
                  selectedAlertId === alert.alert_id
                    ? "border-magenta bg-magenta/10 text-ink"
                    : "border-line bg-surface/40 text-ink-2 hover:border-line-strong"
                }`}
              >
                <span className="font-semibold">{alert.account}</span>
                <span className="ml-2 text-ink-3">{alert.rule_name}</span>
                <RiskBadge score={alert.score} showLabel={false} />
              </button>
            </li>
          ))}
        </ul>
        {selectedAlert ? (
          <div className="mt-3 rounded-lg border border-line/60 bg-surface/40 p-3 text-xs text-ink-2">
            <p>{selectedAlert.explanation}</p>
            <p className="mt-1 text-ink-3">
              evidence: {selectedAlert.evidence_txn_ids.join(", ")}
            </p>
            <p className="mt-1 text-ink-3">{selectedAlert.disclaimer}</p>
          </div>
        ) : null}
      </div>

      <div className="panel p-5">
        <SectionHeader
          title="Transaction Graph"
          subtitle="Synthetic demo data — click nodes and edges to inspect"
          action={<Badge variant="magenta">Demo</Badge>}
        />
        <CytoscapeGraph
          data={graph}
          highlightedTxnIds={highlightedTxnIds}
          height={480}
        />
      </div>

      <div className="panel p-5">
        <SectionHeader
          title="TRACE — Estimated Fund Propagation"
          subtitle="Account-to-account paths with estimated tainted amounts"
        />
        {trace.paths.length === 0 ? (
          <p className="text-sm text-ink-3">No provenance paths returned.</p>
        ) : (
          <ul className="space-y-2">
            {trace.paths.map((path, i) => (
              <li
                key={i}
                className="rounded-lg border border-line/60 bg-surface/40 p-3 text-sm"
              >
                <p className="text-ink">
                  {trace.seed_account} →{" "}
                  {path.steps.map((s) => s.dst).join(" → ")}
                </p>
                <p className="mt-1 text-xs text-ink-2">
                  endpoint {path.endpoint} · estimated tainted{" "}
                  {path.endpoint_tainted.toLocaleString("en-IN")} {path.currency}
                </p>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 border-t border-line pt-2 text-[10px] leading-relaxed text-ink-3">
          {trace.disclaimer}
        </p>
      </div>

      <div className="panel p-5">
        <SectionHeader
          title="CUT — Advisory Recommendations"
          subtitle={`${cut.strategy} strategy · ${
            cut.pct_blocked != null
              ? `${cut.pct_blocked}% estimated blocked`
              : "n/a"
          }`}
        />
        <ul className="space-y-2">
          {cut.recommendations.map((rec) => (
            <li
              key={`${rec.strategy}-${rec.account}`}
              className="rounded-lg border border-line/60 bg-surface/40 p-3 text-sm"
            >
              <p className="font-medium text-ink">
                {rec.account}
                {rec.rank != null ? ` (rank ${rec.rank})` : ""}
              </p>
              <p className="mt-1 text-xs text-ink-2">
                estimated tainted blocked:{" "}
                {rec.estimated_tainted_blocked != null
                  ? rec.estimated_tainted_blocked.toLocaleString("en-IN")
                  : "n/a"}{" "}
                · clean disrupted:{" "}
                {rec.estimated_clean_disrupted != null
                  ? rec.estimated_clean_disrupted.toLocaleString("en-IN")
                  : "n/a"}
              </p>
              {rec.minutes_until_exit != null ? (
                <p className="mt-0.5 text-xs text-ink-3">
                  next exit in ~{Math.round(rec.minutes_until_exit)} min
                </p>
              ) : null}
              <p className="mt-1 text-xs leading-relaxed text-ink-2">
                {rec.rationale}
              </p>
            </li>
          ))}
        </ul>
        <p className="mt-3 border-t border-line pt-2 text-[10px] leading-relaxed text-ink-3">
          {cut.disclaimer}
        </p>
      </div>
    </div>
  );
}

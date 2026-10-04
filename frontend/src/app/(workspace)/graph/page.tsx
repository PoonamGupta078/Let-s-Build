"use client";

import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { api } from "@/lib/api";
import type { GraphData, SeeAlert, TraceData } from "@/lib/types";
import { CytoscapeGraph } from "@/components/graph/CytoscapeGraph";
import { PageHeader } from "@/components/ui/PageHeader";
import { Badge } from "@/components/ui/Badge";
import { Loader } from "@/components/ui/Loader";

const ROLE_LEGEND = [
  { role: "Source", color: "#8b5cf6" },
  { role: "Mule", color: "#d946ef" },
  { role: "Intermediary", color: "#ec4899" },
  { role: "Exit", color: "#f43f5e" },
  { role: "Normal", color: "#64748b" },
];

type Detail =
  | { kind: "node"; id: string }
  | { kind: "edge"; txnId: string }
  | null;

export default function GraphPage() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [alerts, setAlerts] = useState<SeeAlert[]>([]);
  const [trace, setTrace] = useState<TraceData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [selectedAlertId, setSelectedAlertId] = useState("");
  const [showTrace, setShowTrace] = useState(false);
  const [detail, setDetail] = useState<Detail>(null);

  useEffect(() => {
    Promise.all([api.graph(), api.alerts(), api.trace()])
      .then(([g, a, t]) => {
        setGraph(g);
        setAlerts(a);
        setTrace(t);
        setSelectedAlertId(a[0]?.alert_id ?? "");
      })
      .catch((e) => setError(String(e)));
  }, []);

  const filtered = useMemo(() => {
    if (!graph) return null;
    const q = search.trim().toLowerCase();
    if (!q) return graph;
    const nodes = graph.nodes.filter((n) => n.id.toLowerCase().includes(q));
    const ids = new Set(nodes.map((n) => n.id));
    const edges = graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    return { nodes, edges, demo: graph.demo };
  }, [graph, search]);

  const traceTxnIds = useMemo(() => {
    const ids = new Set<string>();
    trace?.paths.forEach((p) => p.steps.forEach((s) => ids.add(s.txn_id)));
    return ids;
  }, [trace]);

  const highlighted = useMemo(() => {
    const ids = new Set<string>();
    const sel = alerts.find((a) => a.alert_id === selectedAlertId);
    sel?.evidence_txn_ids.forEach((t) => ids.add(t));
    if (showTrace) traceTxnIds.forEach((t) => ids.add(t));
    return Array.from(ids);
  }, [alerts, selectedAlertId, showTrace, traceTxnIds]);

  const selectedNode =
    detail?.kind === "node" ? graph?.nodes.find((n) => n.id === detail.id) : undefined;
  const selectedEdge =
    detail?.kind === "edge" ? graph?.edges.find((e) => e.txn_id === detail.txnId) : undefined;

  if (error) return <div className="panel p-5 text-sm text-risk-critical">{error}</div>;
  if (!graph) return <Loader label="Loading graph…" />;

  return (
    <>
      <PageHeader
        title="Graph Explorer"
        subtitle="Interactive fund-flow network — synthetic demo data"
        meta={<Badge variant="magenta">Demo</Badge>}
      />

      <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border border-line bg-surface/40 p-3">
        <label className="relative min-w-52 flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-3" aria-hidden />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search account…"
            className="h-9 w-full rounded-md border border-line bg-glass pl-8 pr-3 text-xs text-ink placeholder:text-ink-3 outline-none focus:border-line-strong"
            aria-label="Search accounts"
          />
        </label>

        <select
          value={selectedAlertId}
          onChange={(e) => setSelectedAlertId(e.target.value)}
          className="h-9 rounded-md border border-line bg-glass px-2 text-xs text-ink outline-none focus:border-line-strong"
          aria-label="Highlight an alert's evidence"
        >
          <option value="">Highlight: none</option>
          {alerts.map((a) => (
            <option key={a.alert_id} value={a.alert_id}>
              {a.account} · {a.rule_name}
            </option>
          ))}
        </select>

        <label className="flex items-center gap-2 text-xs text-ink-2">
          <input
            type="checkbox"
            checked={showTrace}
            onChange={(e) => setShowTrace(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-line bg-glass accent-violet"
          />
          Highlight TRACE paths
        </label>

        <div className="ml-auto flex flex-wrap items-center gap-x-3 gap-y-1">
          {ROLE_LEGEND.map((l) => (
            <span key={l.role} className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-3">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: l.color }} aria-hidden />
              {l.role}
            </span>
          ))}
        </div>
      </div>

      <CytoscapeGraph
        data={filtered}
        highlightedTxnIds={highlighted}
        onNodeClick={(id) => setDetail({ kind: "node", id })}
        onEdgeClick={(txnId) => setDetail({ kind: "edge", txnId })}
        height={540}
      />

      {detail && (
        <div className="panel mt-4 p-4 text-sm text-ink-2">
          {selectedNode ? (
            <div>
              <p className="font-semibold text-ink">{selectedNode.id}</p>
              <p className="mt-1 text-xs">
                role: {selectedNode.role ?? "unknown"}
                {selectedNode.is_exit ? " · exit account" : ""}
              </p>
            </div>
          ) : selectedEdge ? (
            <div>
              <p className="font-semibold text-ink">{selectedEdge.txn_id}</p>
              <p className="mt-1 text-xs">
                {selectedEdge.source} → {selectedEdge.target} ·{" "}
                {selectedEdge.amount.toLocaleString("en-IN")} · {selectedEdge.ts}
              </p>
              {selectedEdge.channel && (
                <p className="mt-0.5 text-xs">channel: {selectedEdge.channel}</p>
              )}
            </div>
          ) : null}
        </div>
      )}
    </>
  );
}


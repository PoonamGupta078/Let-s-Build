"use client";

/**
 * Shared interactive transaction graph (SVG, no external graph library).
 *
 * Renders the nodes/edges returned by GET /api/graph. Clicking a node or edge
 * shows its details; `highlightedTxnIds` (typically an alert's evidence
 * transactions) are drawn with a stronger stroke.
 */
import { useState } from "react";
import type { GraphEdge, GraphNode } from "@/lib/types";

interface TransactionGraphProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedTxnIds?: string[];
}

interface Position {
  x: number;
  y: number;
}

const X_SPACING = 210;
const Y_SPACING = 120;

function layout(nodes: GraphNode[], edges: GraphEdge[]): Map<string, Position> {
  const incoming = new Set(edges.map((e) => e.target));
  const sources = nodes.filter((n) => !incoming.has(n.id)).map((n) => n.id);
  const depth = new Map<string, number>();
  const queue: string[] = [];
  for (const id of sources) {
    depth.set(id, 0);
    queue.push(id);
  }
  while (queue.length > 0) {
    const u = queue.shift()!;
    for (const e of edges.filter((ed) => ed.source === u)) {
      if (!depth.has(e.target)) {
        depth.set(e.target, (depth.get(u) ?? 0) + 1);
        queue.push(e.target);
      }
    }
  }
  for (const n of nodes) {
    if (!depth.has(n.id)) depth.set(n.id, 0);
  }
  const byDepth = new Map<number, string[]>();
  for (const [id, d] of depth) {
    const list = byDepth.get(d) ?? [];
    list.push(id);
    byDepth.set(d, list);
  }
  const positions = new Map<string, Position>();
  for (const [d, ids] of byDepth) {
    ids.forEach((id, i) => {
      positions.set(id, {
        x: 90 + d * X_SPACING,
        y: 90 + (i - (ids.length - 1) / 2) * Y_SPACING,
      });
    });
  }
  return positions;
}

const ROLE_TINT: Record<string, string> = {
  SOURCE: "#a78bfa",
  MULE: "#f472b6",
  INTERMEDIARY: "#f9a8d4",
  DESTINATION: "#facc15",
  EXIT: "#f87171",
  NORMAL: "#94a3b8",
};

const LEGEND: { role: string; tint: string }[] = [
  { role: "Source", tint: ROLE_TINT.SOURCE },
  { role: "Mule", tint: ROLE_TINT.MULE },
  { role: "Intermediary", tint: ROLE_TINT.INTERMEDIARY },
  { role: "Exit", tint: ROLE_TINT.EXIT },
];

type Selection =
  | { kind: "node"; id: string }
  | { kind: "edge"; txnId: string }
  | null;

export function TransactionGraph({
  nodes,
  edges,
  highlightedTxnIds,
}: TransactionGraphProps) {
  const [selected, setSelected] = useState<Selection>(null);
  const positions = layout(nodes, edges);
  const highlight = new Set(highlightedTxnIds ?? []);
  const maxDepth = Math.max(
    0,
    ...Array.from(positions.values()).map((p) => Math.round(p.x / X_SPACING)),
  );
  const width = 90 + maxDepth * X_SPACING + 120;
  const height = 420;

  const selectedNode =
    selected?.kind === "node"
      ? nodes.find((n) => n.id === selected.id)
      : undefined;
  const selectedEdge =
    selected?.kind === "edge"
      ? edges.find((e) => e.txn_id === selected.txnId)
      : undefined;

  return (
    <div className="space-y-4">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full rounded-lg border border-line bg-surface/40"
        role="img"
        aria-label="Transaction graph"
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
          </marker>
        </defs>

        {edges.map((e) => {
          const a = positions.get(e.source);
          const b = positions.get(e.target);
          if (!a || !b) return null;
          const on = highlight.has(e.txn_id);
          return (
            <g
              key={e.txn_id}
              onClick={() => setSelected({ kind: "edge", txnId: e.txn_id })}
              className="cursor-pointer"
            >
              <line
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={on ? "#f43f5e" : "#64748b"}
                strokeWidth={on ? 3 : 1.5}
                markerEnd="url(#arrow)"
              />
              <text
                x={(a.x + b.x) / 2}
                y={(a.y + b.y) / 2 - 6}
                textAnchor="middle"
                fontSize="11"
                fill="#cbd5e1"
              >
                {e.amount.toLocaleString("en-IN")}
              </text>
            </g>
          );
        })}

        {nodes.map((n) => {
          const p = positions.get(n.id);
          if (!p) return null;
          const tint = ROLE_TINT[n.role ?? "NORMAL"] ?? "#94a3b8";
          const on = selected?.kind === "node" && selected.id === n.id;
          return (
            <g
              key={n.id}
              onClick={() => setSelected({ kind: "node", id: n.id })}
              className="cursor-pointer"
            >
              <circle
                cx={p.x}
                cy={p.y}
                r={22}
                fill={tint}
                fillOpacity={0.25}
                stroke={on ? "#ffffff" : tint}
                strokeWidth={on ? 3 : 1.5}
              />
              <text
                x={p.x}
                y={p.y + 4}
                textAnchor="middle"
                fontSize="13"
                fontWeight={600}
                fill="#e2e8f0"
              >
                {n.id}
              </text>
              <text
                x={p.x}
                y={p.y + 32}
                textAnchor="middle"
                fontSize="9"
                fill="#94a3b8"
              >
                {n.role ?? "ACCOUNT"}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {LEGEND.map((item) => (
          <span
            key={item.role}
            className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink-3"
          >
            <span
              className="h-2 w-2 rounded-full"
              style={{ backgroundColor: item.tint }}
              aria-hidden
            />
            {item.role}
          </span>
        ))}
        <span className="ml-auto text-[10px] text-ink-3">
          {nodes.length} accounts · {edges.length} transactions
        </span>
      </div>

      <div className="rounded-lg border border-line/60 bg-surface/40 p-3 text-sm text-ink-2">
        {selectedNode ? (
          <div>
            <p className="font-semibold text-ink">{selectedNode.id}</p>
            <p className="mt-1 text-xs">
              role: {selectedNode.role ?? "unknown"}
              {selectedNode.is_exit ? " · exit" : ""}
            </p>
          </div>
        ) : selectedEdge ? (
          <div>
            <p className="font-semibold text-ink">{selectedEdge.txn_id}</p>
            <p className="mt-1 text-xs">
              {selectedEdge.source} → {selectedEdge.target} ·{" "}
              {selectedEdge.amount.toLocaleString("en-IN")} · {selectedEdge.ts}
            </p>
            {selectedEdge.channel ? (
              <p className="mt-0.5 text-xs">channel: {selectedEdge.channel}</p>
            ) : null}
          </div>
        ) : (
          <p className="text-xs">Select a node or edge to inspect its details.</p>
        )}
      </div>
    </div>
  );
}

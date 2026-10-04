"use client";

import { useEffect, useRef, useState } from "react";
import { Maximize2, Network, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import type cytoscape from "cytoscape";
import type {
  GraphHighlight,
  InvestigationGraphData,
  InvestigationGraphEdge,
  InvestigationGraphNode,
  GraphNodeRole,
} from "@/lib/types";
import { formatINR, formatINRCompact, relativeTime } from "@/lib/format";
import { EmptyState } from "@/components/ui/EmptyState";

/** Role → accent colour, shared by node styling and the legend. */
const ROLE_COLORS: Record<GraphNodeRole, string> = {
  SOURCE: "#8b5cf6", // violet
  MULE: "#d946ef", // magenta
  INTERMEDIARY: "#ec4899", // pink
  DESTINATION: "#38bdf8", // investigating blue
  EXIT: "#f43f5e", // risk-critical
};

const ROLE_LABELS: Record<GraphNodeRole, string> = {
  SOURCE: "Source",
  MULE: "Mule",
  INTERMEDIARY: "Intermediary",
  DESTINATION: "Destination",
  EXIT: "Exit",
};

/** Compact node label: keep the account prefix + last hex chars. */
function shortAccount(id: string): string {
  const hex = id.startsWith("acct_") ? id.slice("acct_".length) : id;
  return `acct_${hex.slice(-6)}`;
}

/** Apply a TRACE highlight to an existing Cytoscape instance. */
function applyHighlight(
  cy: cytoscape.Core,
  highlight: GraphHighlight | null,
): void {
  cy.elements().removeClass("traced subdued");
  if (!highlight) return;

  cy.nodes().forEach((n) => {
    if (highlight.nodeIds.has(n.id())) {
      n.addClass("traced");
    } else {
      n.addClass("subdued");
    }
  });
  cy.edges().forEach((e) => {
    if (highlight.edgeIds.has(e.id())) {
      e.addClass("traced");
    } else {
      e.addClass("subdued");
    }
  });
}

type Selection =
  | { kind: "node"; node: InvestigationGraphNode }
  | { kind: "edge"; edge: InvestigationGraphEdge }
  | null;

interface InvestigationGraphProps {
  data: InvestigationGraphData;
  /** Optional TRACE result highlight: emphasises traced nodes/edges. */
  highlight?: GraphHighlight | null;
}

/**
 * Interactive transaction-network visualisation (Cytoscape.js). Replaces the
 * previous GraphPlaceholder. Reads a deterministic InvestigationGraphData
 * payload so a future GET /api/... graph endpoint can be swapped in without
 * rewriting the visualisation.
 */
export function InvestigationGraph({ data, highlight = null }: InvestigationGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selection, setSelection] = useState<Selection>(null);
  const [error, setError] = useState<string | null>(null);

  const nodeCount = data.nodes.length;
  const edgeCount = data.edges.length;
  const empty = nodeCount === 0 || edgeCount === 0;

  // Apply the TRACE highlight whenever it changes. Highlight starts null and
  // only becomes non-null after a successful trace, by which point the graph
  // has already initialised.
  useEffect(() => {
    const cy = cyRef.current;
    if (cy) applyHighlight(cy, highlight);
  }, [highlight]);

  // Initialise Cytoscape once (browser-only, dynamic import to avoid SSR issues).
  useEffect(() => {
    const container = containerRef.current;
    if (!container || empty) return;

    let cy: cytoscape.Core | null = null;
    let disposed = false;

    (async () => {
      try {
        const cytoscapeMod = await import("cytoscape");
        const cytoscape = cytoscapeMod.default;
        if (disposed || !containerRef.current) return;

        const elements = [
          ...data.nodes.map((n) => ({
            data: {
              id: n.id,
              role: n.role,
              risk: n.risk,
              inflow: n.inflow,
              outflow: n.outflow,
              transactions: n.transactions,
              label: shortAccount(n.id),
            },
          })),
          ...data.edges.map((e) => ({
            data: {
              id: e.id,
              source: e.source,
              target: e.target,
              amount: e.amount,
              currency: e.currency,
              timestamp: e.timestamp,
              label: formatINRCompact(e.amount),
            },
          })),
        ];

        const styles: cytoscape.StylesheetStyle[] = [
          {
            selector: "node",
            style: {
              width: 20,
              height: 20,
              "background-color": "#11122a",
              "border-width": 2,
              "border-color": "#8b5cf6",
              color: "#a9adca",
              "font-size": 9,
              label: "data(label)",
              "text-valign": "bottom",
              "text-margin-y": 5,
              "text-wrap": "ellipsis",
              "text-max-width": "64px",
            },
          },
          ...(Object.keys(ROLE_COLORS) as GraphNodeRole[]).map((role) => ({
            selector: `node[role = "${role}"]`,
            style: { "border-color": ROLE_COLORS[role] },
          })),
          {
            selector: "node.selected",
            style: {
              "border-width": 4,
              "border-color": "#f6f7ff",
              color: "#f6f7ff",
            },
          },
          {
            selector: "edge",
            style: {
              width: 1.5,
              "line-color": "#4a4f73",
              "target-arrow-color": "#4a4f73",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              label: "data(label)",
              color: "#7b7fa3",
              "font-size": 8,
              "text-background-color": "#11122a",
              "text-background-opacity": 0.85,
              "text-background-padding": "2",
            },
          },
          {
            selector: "edge.selected",
            style: {
              width: 3,
              "line-color": "#a855f7",
              "target-arrow-color": "#a855f7",
              color: "#f6f7ff",
              "text-background-color": "#1a1b3a",
            },
          },
          {
            selector: "node.traced",
            style: {
              "border-width": 4,
              "border-color": "#f6f7ff",
              color: "#f6f7ff",
            },
          },
          {
            selector: "edge.traced",
            style: {
              width: 3,
              "line-color": "#d946ef",
              "target-arrow-color": "#d946ef",
              color: "#f6f7ff",
              "text-background-color": "#2a1b3a",
            },
          },
          {
            selector: "node.subdued, edge.subdued",
            style: { opacity: 0.15 },
          },
        ];

        cy = cytoscape({
          container,
          elements,
          style: styles,
          layout: {
            name: "breadthfirst",
            directed: true,
            spacingFactor: 1.15,
            padding: 24,
          },
          wheelSensitivity: 0.2,
          minZoom: 0.25,
          maxZoom: 3,
        });

        cyRef.current = cy;

        const selectNode = (evt: cytoscape.EventObject) => {
          const n = evt.target;
          const found = data.nodes.find((node) => node.id === n.id());
          if (!found) return;
          cyRef.current?.elements().removeClass("selected");
          n.addClass("selected");
          setSelection({ kind: "node", node: found });
        };
        const selectEdge = (evt: cytoscape.EventObject) => {
          const e = evt.target;
          const found = data.edges.find((edge) => edge.id === e.id());
          if (!found) return;
          cyRef.current?.elements().removeClass("selected");
          e.addClass("selected");
          setSelection({ kind: "edge", edge: found });
        };
        const clearSelection = () => {
          cyRef.current?.elements().removeClass("selected");
          setSelection(null);
        };

        cy.on("tap", "node", selectNode);
        cy.on("tap", "edge", selectEdge);
        cy.on("tap", (evt) => {
          if (evt.target === cy) clearSelection();
        });

        // Hover feedback.
        cy.on("mouseover", "node", (evt) => evt.target.addClass("hovered"));
        cy.on("mouseout", "node", (evt) => evt.target.removeClass("hovered"));
        cy.on("mouseover", "edge", (evt) => evt.target.addClass("hovered"));
        cy.on("mouseout", "edge", (evt) => evt.target.removeClass("hovered"));

        cy.fit(undefined, 40);
      } catch (err) {
        if (!disposed) {
          setError(
            err instanceof Error ? err.message : "Failed to initialise graph",
          );
        }
      }
    })();

    return () => {
      disposed = true;
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }
    };
  }, [data, empty]);

  const fit = () => cyRef.current?.fit(undefined, 40);
  const reset = () => {
    cyRef.current?.elements().removeClass("selected");
    setSelection(null);
    cyRef.current?.fit(undefined, 40);
    cyRef.current?.zoom(1);
    cyRef.current?.center();
  };
  const zoomIn = () => {
    const cy = cyRef.current;
    if (cy) cy.zoom(cy.zoom() * 1.25);
  };
  const zoomOut = () => {
    const cy = cyRef.current;
    if (cy) cy.zoom(cy.zoom() / 1.25);
  };

  if (error) {
    return (
      <div className="panel">
        <EmptyState
          icon={Network}
          title="Could not render the transaction network"
          description={error}
        />
      </div>
    );
  }

  if (empty) {
    return (
      <div className="panel">
        <EmptyState
          icon={Network}
          title="No transaction network available"
          description="This investigation has no graph data to display."
        />
      </div>
    );
  }

  return (
    <div className="panel p-5">
      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-ink-2">
            Transaction Network
          </h2>
          <p className="mt-0.5 text-xs tabular-nums text-ink-3">
            {nodeCount} accounts · {edgeCount} transactions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={zoomIn}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-glass text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
            aria-label="Zoom in"
            title="Zoom in"
          >
            <ZoomIn className="h-4 w-4" aria-hidden />
          </button>
          <button
            type="button"
            onClick={zoomOut}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-line bg-glass text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
            aria-label="Zoom out"
            title="Zoom out"
          >
            <ZoomOut className="h-4 w-4" aria-hidden />
          </button>
          <button
            type="button"
            onClick={fit}
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-line bg-glass px-2.5 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
          >
            <Maximize2 className="h-3.5 w-3.5" aria-hidden />
            Fit Graph
          </button>
          <button
            type="button"
            onClick={reset}
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-line bg-glass px-2.5 text-xs font-medium text-ink-2 transition-colors hover:border-line-strong hover:text-ink"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
            Reset View
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div
        ref={containerRef}
        className="h-[420px] w-full overflow-hidden rounded-lg border border-line/60 bg-surface/40"
        role="application"
        aria-label="Transaction network graph"
      />

      {/* Legend */}
      <ul className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2">
        {(Object.keys(ROLE_COLORS) as GraphNodeRole[]).map((role) => (
          <li key={role} className="flex items-center gap-1.5 text-xs text-ink-2">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: ROLE_COLORS[role] }}
              aria-hidden
            />
            {ROLE_LABELS[role]}
          </li>
        ))}
        {highlight && (
          <li className="flex items-center gap-1.5 text-xs font-medium text-magenta">
            <span
              className="h-2.5 w-2.5 rounded-full border border-magenta bg-magenta/30"
              aria-hidden
            />
            Traced path
          </li>
        )}
      </ul>

      {/* Selected entity panel */}
      <div className="mt-4 border-t border-line pt-3">
        {selection === null ? (
          <p className="text-xs text-ink-3">
            Select a node or transaction to inspect
          </p>
        ) : selection.kind === "node" ? (
          <NodeDetails node={selection.node} />
        ) : (
          <EdgeDetails edge={selection.edge} />
        )}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1">
      <dt className="text-[10px] font-semibold uppercase tracking-wider text-ink-3">
        {label}
      </dt>
      <dd className="text-right font-mono text-xs text-ink-2">{value}</dd>
    </div>
  );
}

function NodeDetails({ node }: { node: InvestigationGraphNode }) {
  return (
    <div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-violet">
        Account
      </p>
      <dl className="divide-y divide-line/60">
        <Field label="Account" value={node.id} />
        <Field label="Role" value={ROLE_LABELS[node.role]} />
        <Field label="Risk" value={node.risk} />
        <Field label="Inflow" value={formatINR(node.inflow)} />
        <Field label="Outflow" value={formatINR(node.outflow)} />
        <Field label="Transactions" value={`${node.transactions}`} />
      </dl>
    </div>
  );
}

function EdgeDetails({ edge }: { edge: InvestigationGraphEdge }) {
  return (
    <div>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-magenta">
        Transaction
      </p>
      <dl className="divide-y divide-line/60">
        <Field label="Reference" value={edge.id} />
        <Field
          label="Amount"
          value={`${formatINR(edge.amount)} · ${edge.currency}`}
        />
        <Field label="From" value={edge.source} />
        <Field label="To" value={edge.target} />
        <Field label="Time" value={relativeTime(edge.timestamp)} />
      </dl>
    </div>
  );
}

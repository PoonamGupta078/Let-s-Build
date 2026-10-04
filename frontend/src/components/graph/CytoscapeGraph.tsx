"use client";

/**
 * Shared interactive graph renderer (Cytoscape.js) — the single graph engine
 * used across the Graph Explorer and Investigation workspace.
 *
 * Nodes are coloured/shaped by role (SOURCE/MULE/EXIT/NORMAL); edges are
 * directed, width scales with amount, and edges in `highlightedTxnIds`
 * (SEE evidence / TRACE path transactions) are drawn in red.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape from "cytoscape";
import type { Core, ElementDefinition } from "cytoscape";
import type { GraphData } from "@/lib/types";
import { cn } from "@/lib/utils";

const ROLE_COLORS: Record<string, string> = {
  SOURCE: "#8b5cf6",
  MULE: "#d946ef",
  INTERMEDIARY: "#ec4899",
  DESTINATION: "#38bdf8",
  EXIT: "#f43f5e",
  NORMAL: "#64748b",
};

const ROLE_SHAPES: Record<string, string> = {
  SOURCE: "triangle",
  MULE: "diamond",
  EXIT: "vee",
  INTERMEDIARY: "ellipse",
  DESTINATION: "ellipse",
  NORMAL: "ellipse",
};

type LayoutName = "breadthfirst" | "cose" | "circle" | "concentric";

const LAYOUTS: { id: LayoutName; label: string }[] = [
  { id: "breadthfirst", label: "Flow" },
  { id: "cose", label: "Force" },
  { id: "circle", label: "Circle" },
  { id: "concentric", label: "Ring" },
];

function compactAmount(amount: number): string {
  if (amount >= 1e7) return `${(amount / 1e7).toFixed(2)}Cr`;
  if (amount >= 1e5) return `${(amount / 1e5).toFixed(1)}L`;
  if (amount >= 1e3) return `${(amount / 1e3).toFixed(0)}K`;
  return `${amount.toFixed(0)}`;
}

function buildElements(
  data: GraphData,
  highlighted: Set<string>,
): ElementDefinition[] {
  const elements: ElementDefinition[] = [];
  const amounts = data.edges.map((e) => e.amount).filter((a) => a > 0);
  const maxAmount = amounts.length > 0 ? Math.max(...amounts) : 1;

  for (const node of data.nodes) {
    const role = node.role ?? "NORMAL";
    elements.push({
      data: {
        id: node.id,
        label: node.id,
        role,
        color: ROLE_COLORS[role] ?? ROLE_COLORS.NORMAL,
        shape: ROLE_SHAPES[role] ?? "ellipse",
        is_exit: node.is_exit,
      },
    });
  }

  const nodeIds = new Set(data.nodes.map((n) => n.id));
  for (const edge of data.edges) {
    if (!nodeIds.has(edge.source) || !nodeIds.has(edge.target)) continue;
    const width = 1 + 4 * (edge.amount / maxAmount);
    elements.push({
      data: {
        id: edge.txn_id,
        source: edge.source,
        target: edge.target,
        amount: edge.amount,
        txn_id: edge.txn_id,
        width,
        edgeColor: highlighted.has(edge.txn_id) ? "#f43f5e" : "#475569",
      },
    });
  }
  return elements;
}

interface CytoscapeGraphProps {
  data: GraphData | null;
  highlightedTxnIds?: string[];
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (txnId: string) => void;
  className?: string;
  height?: number;
}

export function CytoscapeGraph({
  data,
  highlightedTxnIds = [],
  onNodeClick,
  onEdgeClick,
  className,
  height = 520,
}: CytoscapeGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const [layout, setLayout] = useState<LayoutName>("breadthfirst");

  const highlighted = useMemo(
    () => new Set(highlightedTxnIds),
    [highlightedTxnIds],
  );
  const elements = useMemo(
    () => (data ? buildElements(data, highlighted) : []),
    [data, highlighted],
  );
  const onNodeClickRef = useRef(onNodeClick);
  const onEdgeClickRef = useRef(onEdgeClick);
  useEffect(() => {
    onNodeClickRef.current = onNodeClick;
  }, [onNodeClick]);
  useEffect(() => {
    onEdgeClickRef.current = onEdgeClick;
  }, [onEdgeClick]);

  useEffect(() => {
    if (!containerRef.current || elements.length === 0) return;

    let cy: Core;
    try {
      cy = cytoscape({
        container: containerRef.current,
        elements,
        wheelSensitivity: 0.3,
        minZoom: 0.2,
        maxZoom: 4,
        style: [
          {
            selector: "node",
            style: {
              "background-color": "data(color)",
              shape: (ele) => ele.data("shape"),
              width: 26,
              height: 26,
              label: "data(label)",
              "font-size": "11px",
              color: "#e2e8f0",
              "text-valign": "bottom",
              "text-margin-y": 6,
              "text-outline-color": "#0a0b1a",
              "text-outline-width": 2,
              "border-width": 1.5,
              "border-color": "data(color)",
            },
          },
          {
            selector: "node:selected",
            style: { "border-width": 3, "border-color": "#ffffff" },
          },
          {
            selector: "edge",
            style: {
              width: "data(width)",
              "line-color": "data(edgeColor)",
              "target-arrow-color": "data(edgeColor)",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              opacity: 0.8,
            },
          },
          {
            selector: "edge:selected",
            style: {
              opacity: 1,
              label: "data(label)",
              "font-size": "9px",
              color: "#94a3b8",
              "text-outline-color": "#0a0b1a",
              "text-outline-width": 1,
            },
          },
        ],
        layout: layoutFor("breadthfirst"),
      });
    } catch (e) {
      console.error("CytoscapeGraph init failed", e);
      return;
    }

    cyRef.current = cy;

    cy.on("tap", "node", (evt) => onNodeClickRef.current?.(evt.target.id()));
    cy.on("tap", "edge", (evt) =>
      onEdgeClickRef.current?.(evt.target.data("txn_id")),
    );
    cy.on("mouseover", "edge", (evt) => {
      const e = evt.target;
      e.style("label", compactAmount(e.data("amount")));
      e.style("opacity", 1);
    });
    cy.on("mouseout", "edge", (evt) => {
      if (!evt.target.selected()) evt.target.style("label", "");
    });
    cy.on("layoutstop", () => {
      if (cyRef.current) cyRef.current.fit(undefined, 30);
    });

    return () => {
      try {
        cy.destroy();
      } catch {
        /* ignore */
      }
      cyRef.current = null;
    };
  }, [elements]);

  const runLayout = (name: LayoutName) => {
    setLayout(name);
    cyRef.current?.layout(layoutFor(name) as cytoscape.LayoutOptions).run();
  };

  const fit = () => cyRef.current?.fit(undefined, 30);

  if (!data || data.nodes.length === 0) {
    return (
      <div
        className={cn(
          "flex items-center justify-center rounded-lg border border-line bg-surface/40 text-sm text-ink-3",
          className,
        )}
        style={{ height }}
      >
        No graph data to display
      </div>
    );
  }

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex flex-wrap items-center gap-1.5">
        {LAYOUTS.map((l) => (
          <button
            key={l.id}
            type="button"
            onClick={() => runLayout(l.id)}
            className={cn(
              "rounded-md border px-2.5 py-1 text-[11px] font-medium transition-colors",
              layout === l.id
                ? "border-violet/40 bg-violet/15 text-violet"
                : "border-line bg-glass text-ink-2 hover:border-line-strong hover:text-ink",
            )}
          >
            {l.label}
          </button>
        ))}
        <button
          type="button"
          onClick={fit}
          className="ml-auto rounded-md border border-line bg-glass px-2.5 py-1 text-[11px] font-medium text-ink-2 hover:border-line-strong hover:text-ink"
        >
          Fit
        </button>
      </div>
      <div
        ref={containerRef}
        className="w-full rounded-lg border border-line bg-surface/40"
        style={{ height }}
      />
    </div>
  );
}

function layoutFor(name: LayoutName): cytoscape.LayoutOptions {
  switch (name) {
    case "circle":
      return { name: "circle", animate: false, spacingFactor: 1.4 };
    case "concentric":
      return { name: "concentric", animate: false, minNodeSpacing: 60 };
    case "cose":
      return {
        name: "cose",
        animate: false,
        idealEdgeLength: () => 100,
        nodeRepulsion: () => 6000,
        gravity: 0.35,
        numIter: 40,
        randomize: false,
      };
    case "breadthfirst":
    default:
      return {
        name: "breadthfirst",
        animate: false,
        directed: true,
        spacingFactor: 1.25,
      };
  }
}


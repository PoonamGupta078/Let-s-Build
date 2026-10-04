"use client";

import { useState } from "react";
import type { Investigation, GraphHighlight } from "@/lib/types";
import { InvestigationGraph } from "@/components/investigation/InvestigationGraph";
import { TracePanel } from "@/components/investigation/TracePanel";

/**
 * Primary investigation surface: the transaction graph plus the TRACE stage.
 * Owns the TRACE highlight so a successful trace is reflected on the graph.
 */
export function TraceSection({
  investigation,
}: {
  investigation: Investigation;
}) {
  const [highlight, setHighlight] = useState<GraphHighlight | null>(null);

  return (
    <div className="space-y-6">
      <InvestigationGraph data={investigation.graph} highlight={highlight} />
      <TracePanel investigation={investigation} onHighlight={setHighlight} />
    </div>
  );
}
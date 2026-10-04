/**
 * Mapping layer: TRACE response → graph highlight model.
 *
 * Keeps the TRACE response shape out of the graph component. A future real
 * backend response can be mapped here without touching the visualisation.
 */
import type { GraphHighlight } from "@/lib/types";
import type { TraceResult } from "@/lib/api/trace";

/**
 * Build a graph highlight from a TRACE result: every node id reachable via
 * tainted accounts + path steps, and every edge (transaction) id present in
 * tainted_edges + path steps. Only ids actually returned by TRACE are
 * highlighted — nothing is invented.
 */
export function traceResultToHighlight(result: TraceResult): GraphHighlight {
  const nodeIds = new Set<string>();
  const edgeIds = new Set<string>();

  nodeIds.add(result.seed_account);
  for (const account of Object.keys(result.tainted_accounts)) {
    nodeIds.add(account);
  }
  for (const txnId of Object.keys(result.tainted_edges)) {
    edgeIds.add(txnId);
  }
  for (const path of result.paths) {
    for (const step of path.steps) {
      nodeIds.add(step.src);
      nodeIds.add(step.dst);
      edgeIds.add(step.txn_id);
    }
  }

  return { nodeIds, edgeIds };
}

/** True when a TRACE result contains no propagating fund-flow at all. */
export function isTraceEmpty(result: TraceResult): boolean {
  const accountsBeyondSeed = Object.keys(result.tainted_accounts).filter(
    (a) => a !== result.seed_account,
  );
  return (
    accountsBeyondSeed.length === 0 &&
    Object.keys(result.tainted_edges).length === 0 &&
    result.paths.length === 0
  );
}
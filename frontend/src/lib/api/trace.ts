/**
 * TRACE API adapter (frontend → backend).
 *
 * IMPORTANT — the backend has NO HTTP API yet. TRACE is implemented in
 * `trace/run.py` as pure Python functions (`trace()`, `trace_from_alert()`)
 * returning a `TraceResult` dataclass; `api/` is empty and there are no
 * FastAPI routes. This adapter therefore defines the request/response types
 * against the real `TraceResult`/`TraceStep`/`TracePath` dataclass shape and
 * exposes `traceInvestigation()`, but the call will surface a clear
 * "backend unavailable" state until the API layer exists. It NEVER fabricates
 * trace results.
 */
import { getApiBaseUrl } from "@/lib/api/config";

/** Client request for TRACE. Mirrors trace.run.trace()'s caller-supplied args. */
export interface TraceRequest {
  /** Pseudonymised seed (source) account id. */
  seedAccount: string;
  /** Seed amount in rupees; must be > 0 (validated before sending). */
  seedAmount: number;
  /** Seed timestamp (ISO-8601). */
  seedTs: string;
  /** Optional seed currency; required when the seed spans multiple currencies. */
  seedCurrency?: string;
  /** "per_currency" (default) or "single". */
  currencyMode?: "per_currency" | "single";
  /** Max greedy provenance paths to return (>= 1). */
  maxPaths?: number;
  /** Exit account ids for exit-taint reporting. */
  exits?: string[];
}

/** One hop in a provenance path (mirrors trace.models.TraceStep). */
export interface TraceStep {
  txn_id: string;
  src: string;
  dst: string;
  ts: string;
  amount: number;
  currency: string;
  tainted_amount: number;
  allocation_ratio: number;
  reason: string;
}

/** One greedy provenance path (mirrors trace.models.TracePath). */
export interface TracePath {
  endpoint: string;
  endpoint_tainted: number;
  currency: string;
  steps: TraceStep[];
  greedy: boolean;
}

/** Full TRACE result (mirrors trace.models.TraceResult.to_dict()). */
export interface TraceResult {
  alert_id: string;
  seed_account: string;
  seed_amount: number;
  seed_currency: string;
  seed_ts: string;
  config: {
    currency_mode: string;
    max_paths: number;
    min_tainted_threshold: number;
    [key: string]: unknown;
  };
  /** account -> { currency -> tainted amount }. */
  tainted_accounts: Record<string, Record<string, number>>;
  /** txn_id -> tainted amount. */
  tainted_edges: Record<string, number>;
  /** currency -> total tainted reaching requested exit accounts. */
  exit_taint_by_currency: Record<string, number>;
  paths: TracePath[];
  disclaimer: string;
}

export class TraceBackendUnavailableError extends Error {
  constructor() {
    super(
      "TRACE backend unavailable. Start the investigation API to execute TRACE.",
    );
    this.name = "TraceBackendUnavailableError";
  }
}

export class TraceRequestError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = "TraceRequestError";
  }
}

export class TraceResponseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "TraceResponseError";
  }
}

/** Minimal runtime validation of an unknown JSON payload → TraceResult. */
function parseTraceResult(json: unknown): TraceResult {
  if (typeof json !== "object" || json === null) {
    throw new TraceResponseError("Malformed TRACE response (not an object)");
  }
  const r = json as Record<string, unknown>;
  if (typeof r.seed_account !== "string" || typeof r.seed_ts !== "string") {
    throw new TraceResponseError("Malformed TRACE response (missing seed fields)");
  }
  if (typeof r.tainted_accounts !== "object" || r.tainted_accounts === null) {
    throw new TraceResponseError("Malformed TRACE response (missing tainted_accounts)");
  }
  if (typeof r.tainted_edges !== "object" || r.tainted_edges === null) {
    throw new TraceResponseError("Malformed TRACE response (missing tainted_edges)");
  }
  if (!Array.isArray(r.paths)) {
    throw new TraceResponseError("Malformed TRACE response (missing paths)");
  }
  return json as TraceResult;
}

/**
 * Execute TRACE for an investigation.
 *
 * When no API base URL is configured (the current state — there is no backend
 * HTTP API), this throws TraceBackendUnavailableError rather than fabricating
 * a result.
 */
export async function traceInvestigation(
  request: TraceRequest,
): Promise<TraceResult> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new TraceBackendUnavailableError();
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/trace`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });
  } catch {
    throw new TraceBackendUnavailableError();
  }

  if (response.status >= 400 && response.status < 500) {
    throw new TraceRequestError(
      `TRACE request was rejected (HTTP ${response.status}).`,
      response.status,
    );
  }
  if (!response.ok) {
    throw new TraceBackendUnavailableError();
  }

  const json: unknown = await response.json().catch(() => {
    throw new TraceResponseError("Malformed TRACE response (not JSON)");
  });
  return parseTraceResult(json);
}
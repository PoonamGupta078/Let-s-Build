/**
 * Frontend API configuration.
 *
 * NOTE: the Fraud Detector backend currently has NO HTTP API. `api/` contains
 * only an empty `__init__.py` — there is no FastAPI app, no routes, and no
 * `api/schemas.py` / `docs/api_contract.md`. The TRACE engine lives in
 * `trace/run.py` as pure Python functions (not exposed over HTTP).
 *
 * This module centralises the (future) API base URL so the rest of the
 * frontend has a single, clean seam for when the API layer is added. Until a
 * base URL is configured, API calls surface "backend unavailable" — they never
 * fabricate results.
 */

/** API base URL, e.g. "http://localhost:8000". Undefined when not configured. */
export function getApiBaseUrl(): string | undefined {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL;
  return value && value.trim() !== "" ? value.trim().replace(/\/+$/, "") : undefined;
}
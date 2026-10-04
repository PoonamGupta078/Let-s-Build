# API Contract — SecureTrace backend

Read-only FastAPI backend over the existing **SEE** / **TRACE** / **CUT** engines
and the transaction graph builder. It serves a deterministic synthetic case
(`data/make_case.py`, seed 42, no background rows), so it needs no Neo4j,
credentials, or the full 4.5M-row IBM dataset.

- Base URL: `http://localhost:8000`
- Run: `python -m uvicorn api.main:app --reload --port 8000`
- CORS: enabled for `http://localhost:3000` (the Next.js dev server)

## Endpoints

### `GET /api/health`
Service status. Returns `{ status, service, version, demo_mode, data_source }`.

### `GET /api/alerts`
Runs SEE detection on the synthetic case and returns all alerts.

| Field | Type | Meaning |
|---|---|---|
| `alert_id` | string | deterministic id |
| `rule_id` / `rule_name` | string | rule that fired (RPT001 / HTA001 / FAN001) |
| `account` | string | flagged account |
| `score` | int | 0–100 heuristic (not a probability) |
| `window_start` / `window_end` | string | ISO timestamps |
| `evidence_txn_ids` | string[] | supporting transaction ids |
| `explanation` | string | human-readable facts + thresholds |
| `disclaimer` | string | "investigative lead only…" |

### `GET /api/graph`
Transaction graph. **Neo4j-backed** when Neo4j is configured and the demo case is
loaded (see `scripts/load_demo_neo4j.py`); otherwise falls back to an in-memory
`graph/build.py` build. Both return the same shape.

- `nodes`: `{ id, role, is_exit }`
- `edges`: `{ txn_id, source, target, amount, ts, channel, type }`

### `GET /api/trace?seed_account=S`
TRACE estimated fund propagation.

- `tainted_accounts`: `{ account: { currency: amount } }`
- `exit_taint_by_currency`: `{ currency: amount }`
- `paths`: greedy provenance paths, each with `steps` (txn_id, src, dst, ts,
  amount, currency, tainted_amount, allocation_ratio, reason)
- `disclaimer`: taint estimates are leads, not proof of physical fund movement

### `GET /api/cut?seed_account=S&t_alert=2026-01-01T10:20:00`
CUT advisory intervention recommendations.

- `strategy`, `pct_blocked`, `recommendations`
- each recommendation: `account`, `rank`, `estimated_tainted_blocked`,
  `estimated_clean_disrupted`, `minutes_until_exit`, `rationale`
- `disclaimer`: advisory only — no holds executed

## Notes

- Synthetic demo data only — not production data.
- No endpoint executes a freeze or writes to a database.
- Fund propagation is estimated; money is fungible.
- Unknown seed account returns `404`.

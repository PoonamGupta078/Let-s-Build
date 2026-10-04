# CUT — Advisory Intervention Recommendation Engine

## Public API

```python
from cut.config import CutConfig
from cut.run import recommend, recommend_from_trace

result = recommend(txns, seeds, exits, t_alert, config=None, seed_currency=None)
result = recommend_from_trace(txns, trace_result, exits, t_alert, config=None)
```

## Strategies

### Greedy (`strategy="greedy"`, default)

Uses `core.freeze.plan()`: greedy marginal-gain selection of accounts.
Each iteration simulates freezing one account at `t_alert` and measures the
reduction in tainted funds reaching exits.  Selects up to
`max_recommendations` accounts ranked by score =
`tainted_blocked / (clean_disrupted + hold_cost + 1.0)`.

**Not globally optimal.** Each recommendation includes rank, per-account
tainted blocked, clean disrupted, ETA, and evidence txn_ids.

### Block-all (`strategy="block_all"`)

Uses `core.freeze.block_all()`: weighted minimum vertex cut on the
post-alert tainted-flow graph.  Returns an **unranked** cut-set.  Per-account
metrics (tainted blocked, clean disrupted, ETA, evidence) are set to `None`
because the min-cut algorithm does not produce per-account breakdowns.
Only the aggregate `clean_held` is reported.

## Currency policy

- **No currency column:** runs once with the documented single-currency
  assumption.  If ``seed_currency`` is supplied, it is recorded; otherwise
  ``"UNKNOWN"`` is used.  No FX conversion is performed.
- **Currency column present, single value:** accepts the input.  If
  ``seed_currency`` is supplied, it must match the value in the data.
  If omitted, the currency is inferred from the data automatically.
- **Currency column present, multiple values:** raises ``ValueError``.
  CUT requires a single currency per run — the caller must filter the
  transaction data before calling.
- **Currency column present, all null/NaN:** raises ``ValueError`` unless
  ``seed_currency`` is supplied, in which case it is used as the label.
- **``recommend_from_trace()``** validates that ``trace_result.seed_currency``
  matches the transaction data's currency and raises ``ValueError`` on conflict.

## Output models

### `CutRecommendation`

| Field | Type | Description |
|---|---|---|
| account | str | Account to investigate |
| rank | int or None | 1 = highest priority. None for block_all (unranked) |
| strategy | str | "greedy" or "block_all" |
| evidence_txn_ids | tuple[str, ...] | Tainted transactions through this account |
| estimated_tainted_blocked | float or None | Estimated tainted $ blocked (None for block_all) |
| estimated_clean_disrupted | float or None | Estimated clean $ disrupted (None for block_all) |
| minutes_until_exit | float or None | ETA to next tainted exit (None for block_all) |
| rationale | str | Human-readable explanation |
| currency | str | Currency of this recommendation |

### `CutResult`

| Field | Type |
|---|---|
| strategy | str |
| seed_accounts | tuple[str, ...] |
| exit_accounts | tuple[str, ...] |
| baseline_exit_taint | float |
| total_tainted_blocked | float |
| pct_blocked | float or None (None when baseline=0) |
| recommendations | tuple[CutRecommendation, ...] |
| config | dict |
| aggregate_clean_held | float or None (block_all only) |
| disclaimer | str |

## Safety

- **Advisory only.** No holds are executed, no database writes.
- `pct_blocked` is `None` when baseline exit taint is zero (avoids 0/0).
- All amounts are estimates, not guaranteed recoveries.
- `recommend_from_trace()` extracts seed from `TraceResult` directly.
  Does NOT infer seed from alert score.

## Disclaimers

The `disclaimer` field states that recommendations are advisory only,
all amounts are estimates, and the investigator makes the final decision.

## What CUT does NOT do

- Does NOT execute holds or freeze accounts.
- Does NOT modify `core/freeze.py` or `core/taint.py`.
- Does NOT use Neo4j.
- Does NOT perform FX conversion.
- Does NOT infer seed amounts from alert scores.
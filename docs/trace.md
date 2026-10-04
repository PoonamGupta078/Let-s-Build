# TRACE — Time-Respecting Fund-Flow Propagation

## Public API

```python
from trace.config import TraceConfig
from trace.run import trace, trace_from_alert

result = trace(txns, seed_account, seed_ts, seed_amount,
               config=None, seed_currency=None, exits=None)

result = trace_from_alert(txns, alert, seed_ts, seed_amount,
                          config=None, seed_currency=None, exits=None)
```

## Required input schema

`txns` must contain at minimum: `txn_id`, `ts`, `src`, `dst`, `amount`.
Optional: `currency` (string column; required for `per_currency` mode).

The DataFrame is **never mutated**.

## Currency policy

- **`per_currency` (default):** taint propagates independently within each
  currency. A seed in USD never propagates through EUR transactions.
  No implicit FX conversion is performed.
- **`single`:** all amounts treated as fungible. The caller asserts that
  all amounts share one currency. This assertion is recorded in the result
  config.
- If `seed_currency` is omitted and the seed account appears with multiple
  currencies, `trace()` raises `ValueError`.
- If no `currency` column exists and `seed_currency` is omitted, `trace()`
  raises `ValueError`.

## Output model

`tainted_accounts`: `dict[account, dict[currency, amount]]` — per-currency
taint, never summed across currencies.

`exit_taint_by_currency`: `dict[currency, amount]` — total tainted amount
reaching the requested exit accounts, by currency. Empty when no exits
provided.

`paths`: tuple of `TracePath` — greedy provenance paths from seed to
exit accounts. Only populated when `exits` is provided. Each path has
`greedy=True` indicating it uses `core.taint.top_paths()` (largest earlier
tainted inflow at each step, not globally optimal).

## Haircut allocation formula

When an outgoing transaction exceeds the recorded balance:

```
effective_balance = max(recorded_balance, outgoing_amount)
ratio = tainted[effective_balance] / effective_balance
tainted_out = ratio * outgoing_amount
```

This assumes additional clean funds *may* be available. It is a modeling
assumption, not evidence that those funds exist.

## Seed semantics

- `seed_amount` must be finite and strictly positive.
- `seed_ts` must be a valid `Timestamp`, not `NaT`.
- One seed per `trace()` call. Multi-seed is a copilot/API concern.
- `trace_from_alert()` requires the caller to supply `seed_ts` and
  `seed_amount`. These are NOT inferred from the alert's score.

## Self-transfers, cycles, timestamps

- **Self-transfers (A→A):** processed normally. Tainted leaves and returns
  in same amount; net effect is zero. Balance is preserved.
- **Cycles (A→B→C→A):** processed in timestamp order. Each loop iteration
  reduces tainted due to the haircut. Terminates naturally.
- **Transactions before seed:** zero taint from that seed.
- **Out-of-order rows:** sorted by `(ts, txn_id)` before processing.
- **Equal timestamps:** deterministic (stable sort by txn_id).
- **Duplicate txn_ids:** rejected with `ValueError`.
- **Zero-amount transactions:** taint propagation is zero (ratio × 0 = 0).
- **Missing/NaN/NaT values:** rejected with `ValueError`.

## Disclaimers

The `disclaimer` field on `TraceResult` states that taint estimates are
investigative leads under a stated accounting policy, not proof that
specific physical funds moved or that an account committed a crime.

## What TRACE v1 does NOT do

- Does NOT use Neo4j (all computation is Python/DataFrames).
- Does NOT perform FX conversion.
- Does NOT model transaction fees (no fee field in IBM data).
- Does NOT modify `core/taint.py` or `core/freeze.py`.

## Accounting invariants tested

- Estimated taint per transaction ≤ transaction amount.
- Tainted balance never becomes materially negative.
- Repeated outgoing transactions do not repeatedly spend the same tainted
  balance.
- Total tainted across all accounts ≤ seed amount (conservation).
- Results are deterministic across repeated calls.
 

# SEE Detection Engine — Documentation

## Overview

SEE (Suspicious Entity Evaluation) is a deterministic, rule-based detection
engine.  It scans normalised transactions and emits **investigative leads**
(not proof of wrongdoing).  Every alert carries structured evidence
(transaction IDs, thresholds, explanations) and a disclaimer.

## Implemented rules

| ID     | Name                   | What it detects |
|--------|------------------------|-----------------|
| RPT001 | Rapid pass-through     | Funds received and sent onward within a configurable time window, matched by currency. |
| HTA001 | High transaction activity | Transaction count exceeds a configurable threshold within a time window. |
| FAN001 | Fan-in/fan-out         | More than a configurable number of distinct counterparties within a time window. |

## Configuration (SeeConfig)

All thresholds are in `see/run.py::SeeConfig`:

```
rapid_window          = 24 hours    (max elapsed time for RPT match)
rapid_min_amount_ratio= 0.0         (min out/in amount ratio)
activity_window       = 24 hours    (counting window for HTA)
activity_threshold    = 10          (min txn count for HTA)
fan_window            = 24 hours    (counting window for FAN)
fan_threshold         = 10          (min distinct counterparties for FAN)
```

All windows must be strictly positive. Thresholds must be >= 1. Ratios must
be >= 0. Invalid values raise `ValueError` at construction time.

## Input contract

`detect()` expects validated, ingestion-pipeline output. It enforces:

- **Required columns:** txn_id, ts, src, dst, amount. Missing → `ValueError`.
- **No NaT timestamps:** Rows with unparseable or missing timestamps are
  rejected with `ValueError` (not silently skipped).
- **No duplicate txn_ids:** Duplicate IDs violate the validated-input contract
  and are rejected with `ValueError`.
- **Caller immutability:** The input DataFrame is never mutated.
- **Stable ordering:** Timestamps are sorted with `kind="mergesort"` so that
  equal timestamps preserve their original row order.

## Alert schema

Every `Alert` (see `see/models.py`) contains:

- `alert_id` — deterministic SHA-256 hash of (rule_id, account, evidence).
- `rule_id`, `rule_name` — which rule produced the alert.
- `account` — the flagged account.
- `score` — heuristic 0-100; higher = more suspicious.  NOT a probability.
- `window_start`, `window_end` — ISO timestamps of the detection window.
- `evidence_txn_ids` — the specific transaction IDs that support the alert.
- `explanation` — human-readable summary of observed facts and thresholds.
- `disclaimer` — fixed text: "This alert is an investigative lead only…".

Output is JSON-serialisable and deterministic for the same inputs.

## Quick start

```python
from see import detect, SeeConfig
import pandas as pd

# txns must have: txn_id, ts, src, dst, amount (+ optional currency)
alerts = detect(txns_df, SeeConfig(rapid_window=pd.Timedelta(hours=1)))
for alert in alerts:
    print(alert.alert_id, alert.rule_name, alert.score, alert.explanation)
```

## Limitations and false-positive risks

- Money is fungible: RPT matches by currency, not by exact fund tracing.
- **One outgoing, many incoming:** A single outgoing transaction may appear
  in multiple RPT alerts if separate incoming transactions independently
  satisfy the rule within the window.  This is by design — each incoming
  transaction is independently suspicious.
- At the exact window boundary (elapsed == window), RPT emits an alert with
  score 0.  This is intentional: the alert still exists but has minimal
  urgency.  Score semantics: higher = more suspicious.
- Self-transfers (A→A) are handled as normal transactions; policy is
  controlled at ingestion time, not here.
- Fan-in/fan-out intentionally combines incoming and outgoing counterparties.
- Amounts in different currencies are never compared.
- Rules are heuristic; high scores do not imply laundering.
- The engine does not use ground-truth labels (`is_laundering`, `Is Laundering`)
  in any way.  Labels exist only in `data/processed/labels.csv` for
  evaluation purposes.

## Separation from evaluation labels

Detection inputs (`data/processed/transactions.csv`) never contain
laundering labels.  Labels live in a separate file
(`data/processed/labels.csv`) and are never read by the SEE module.

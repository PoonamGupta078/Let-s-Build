# ML Baseline and GNN — Experiment Report

## Dataset

| Field | Value |
|---|---|
| Source | `data/processed/transactions.csv` (IBM AML HI-Small) |
| Rows | 4,487,133 |
| Positive labels | 5,166 (0.115%) |
| Label file | `data/processed/labels.csv` (never used as features) |
| Time range | 2022-09-01 to 2022-09-18 |

## Chronological split

| Split | Boundary | Full-data rows | Full-data positives |
|---|---|---|---|
| Train | ≤ 2022-09-14 23:59:59 | 4,487,057 | 5,091 |
| Val | ≤ 2022-09-16 23:59:59 | 54 | 53 |
| Test | > 2022-09-16 23:59:59 | 22 | 22 |

**Critical limitation:** The chronological split produces extremely small
validation and test sets with almost no negative examples.  The positive
labels are clustered in the last two days.  All models achieve near-perfect
scores because val/test are overwhelmingly positive-only.  A stratified
temporal split or oversampling strategy is needed for meaningful evaluation.

## Features (30 total)

| Category | Features |
|---|---|
| Transaction-level | `log1p(amount)`, `hour`, `day_of_week`, `is_weekend` |
| Categorical (one-hot) | `channel` (6 values), `currency` (15 values) |
| Boolean | `ext_bank` |
| Historical (24h window) | `src_count`, `src_amt_mean`, `dst_count` |

Encoders/scalers fitted on training data only.  No label-derived features.

## Full-data baseline results

| Model | Val F1 | Test PR-AUC | Test F1 | Train time |
|---|---|---|---|---|
| Dummy | 0.9907 | 1.0 | 1.0 | 0.93s |
| Logistic | 0.9907 | 1.0 | 1.0 | 13.84s |
| HGB | 0.9907 | 1.0 | 1.0 | 73.85s |

## GNN results (200k sample)

| Metric | Value |
|---|---|
| Architecture | 2-layer GCN (numpy, no PyTorch) |
| Hidden dim | 32, epochs 30 |
| Nodes | 177,144 |
| Train edges | 199,997 |
| Train time | 102.33s |
| Test PR-AUC | 1.0 (same caveat — tiny split) |

## Leakage safeguards

- Labels stored separately, never in features.
- Historical features use `closed="left"` rolling windows.
- Encoders fitted on train only.
- Threshold selected on validation only.

## Artifacts

- `artifacts/results/full_report.json`
- `artifacts/models/*.pkl`

## Known limitations

1. Chronological split produces tiny val/test with near-zero negatives.
2. `src_unique_dst` stubbed to 0 (slow rolling-nunique on strings).
3. No PyTorch — GNN uses numpy-based GCN.
4. No Neo4j integration for ML features.
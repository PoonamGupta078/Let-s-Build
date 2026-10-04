# ML Baseline and GNN — Experiment Report

## Dataset

| Field | Value |
|---|---|
| Source | `data/processed/transactions.csv` (IBM AML HI-Small) |
| Rows | 4,487,133 |
| Positive labels | 5,166 (0.115%) |
| Label file | `data/processed/labels.csv` (never used as features) |
| Time range | 2022-09-01 to 2022-09-18 |

## Chronological split (CORRECTED — percentile-based)

The split boundaries are computed from the data at the 80th and 90th
percentile timestamps (not hardcoded dates). Identical timestamps are kept
together to prevent same-time information leakage.

| Split | Boundary | Rows | Positives | Negatives |
|---|---|---|---|---|
| Train | ≤ 2022-09-08 21:16:00 | 3,589,879 (80%) | 3,513 | 3,586,366 |
| Val | ≤ 2022-09-09 14:38:00 | 448,641 (10%) | 346 | 448,295 |
| Test | > 2022-09-09 14:38:00 | 448,613 (10%) | 1,307 | 447,306 |

**Row-loss guarantee:** 3,589,879 + 448,641 + 448,613 = 4,487,133 (exact).
All rows appear in exactly one split; no overlap; no discard.

> **Label-distribution caveat:** the earlier claim that laundering labels are
> "concentrated in the final two days" is **unverified**. The recorded split-level
> counts support only a *higher positive rate in the later test period*
> (test 0.291% vs train 0.098%). The precise per-day label distribution has not
> been independently verified. This split is chronological and row-loss-free, but
> it is not claimed to be perfectly representative of future real-world data.

## Features (30 total)

| Category | Features |
|---|---|
| Transaction-level | `log1p(amount)`, `hour`, `day_of_week`, `is_weekend` |
| Categorical (one-hot) | `channel` (6 values), `currency` (15 values) |
| Boolean | `ext_bank` |
| Historical (24h window) | `src_count`, `src_amt_mean`, `dst_count` |

Encoders/scalers fitted on training data only. No label-derived features.
Historical features use `closed="left"` rolling windows (strictly earlier).

## Full-data baseline results (CORRECTED)

| Model | Val PR-AUC | Test PR-AUC | Test ROC-AUC | Test F1 | Test Precision | Test Recall | Train time |
|---|---|---|---|---|---|---|---|
| Dummy | 0.0015 | 0.0029 | 0.5000 | 0.0058 | 0.0029 | 1.0000 | 0.49s |
| Logistic | 0.0067 | 0.0067 | 0.7865 | 0.0202 | 0.0106 | 0.2334 | 6.33s |
| HGB | 0.0133 | 0.0133 | 0.5695 | 0.0334 | 0.0187 | 0.1561 | 21.86s |

Notes:
- Dummy PR-AUC ≈ positive rate (0.0029) as expected for a random classifier;
  its ROC-AUC is 0.5, also as expected for a random classifier.
- Logistic and HGB beat the dummy baseline but are weak (PR-AUC < 0.02),
  an honest result given the extreme imbalance and simple features.
- Logistic's ROC-AUC (0.7865) suggests a ranking signal, but HGB's (0.5695) is
  near random — the two models rank differently despite similarly low PR-AUC.
- The previous "PR-AUC 1.0" was an artifact of the degenerate hardcoded
  split (54 val / 22 test rows, nearly all positive). Corrected above.

## GNN results (100k sample)

| Metric | Value |
|---|---|
| Architecture | 2-layer GCN (numpy, no PyTorch) |
| Hidden dim | 32, epochs 30 |
| Device | CPU |
| Nodes | 120,405 |
| Train edges | 80,002 |
| Train time | 14.42s |
| Val PR-AUC | 0.0148 (ROC-AUC 0.7648) |
| Test PR-AUC | 0.0107 (ROC-AUC 0.7606) |
| Threshold-selected test recall | 0 / 28 positives (threshold 0.6399) |

Note: The GNN learns a ranking signal (ROC-AUC ~0.76, well above the 0.5 random
baseline), but the validation-selected threshold detected **0** of the 28 positive
test examples because the validation set has only **7** positives. With so few
positive validation examples, threshold calibration is unstable: the threshold
(0.6399) that maximised validation F1 produced an all-negative test prediction.
This is a threshold-calibration limitation, not a leakage issue — the ranking
metrics (PR-AUC / ROC-AUC) show the model is learning, but they do **not** prove
practical fraud-detection effectiveness.

## Leakage safeguards

- Labels stored separately, never in features.
- Historical features use `closed="left"` rolling windows (strictly earlier).
- Identical timestamps kept together in splits.
- Encoders fitted on train only.
- Threshold selected on validation only, never tuned on test.

## Artifacts

- `artifacts/results/full_report.json`
- `artifacts/models/*.pkl`

## Known limitations

1. `src_unique_dst` feature is stubbed to 0 (slow rolling-nunique on strings).
2. No PyTorch — GNN uses numpy-based GCN.
3. No Neo4j integration for ML features.
4. Models are weak (PR-AUC < 0.02) — expected for a first baseline with
   extreme class imbalance; not a production-grade detector.
5. Validation set has only 7–346 positives (depending on full-data vs sample),
   so validation-selected thresholds are unstable and may yield 0 test recall
   even when ROC-AUC shows the model is learning.
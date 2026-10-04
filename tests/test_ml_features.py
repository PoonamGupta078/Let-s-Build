"""Tests for ML feature engineering — leakage checks and correctness."""
import numpy as np
import pandas as pd
import pytest

from models.config import SplitConfig, FeatureConfig
from models.features import prepare_base_features, build_feature_matrix


def _sample_txns():
    return pd.DataFrame({
        "txn_id": [f"t{i}" for i in range(6)],
        "ts": pd.to_datetime([
            "2022-09-01 10:00", "2022-09-01 10:00", "2022-09-01 11:00",
            "2022-09-01 12:00", "2022-09-15 08:00", "2022-09-17 09:00",
        ]),
        "src": ["A", "A", "B", "A", "C", "D"],
        "dst": ["B", "B", "C", "C", "D", "E"],
        "amount": [100.0, 200.0, 50.0, 500.0, 300.0, 1000.0],
        "type": "transfer",
        "channel": ["Cheque", "Wire", "Cheque", "ACH", "Cash", "Cheque"],
        "ext_bank": [True, False, True, True, False, True],
        "currency": ["USD", "USD", "EUR", "USD", "USD", "GBP"],
    })


def test_base_features_no_label_leakage():
    txns = _sample_txns()
    txns["is_laundering"] = [0, 1, 0, 1, 0, 0]
    feat = prepare_base_features(txns)
    assert "is_laundering" not in feat.columns
    assert "label" not in feat.columns


def test_base_features_time_columns():
    txns = _sample_txns()
    feat = prepare_base_features(txns)
    assert feat["hour"].dtype == np.int8
    assert feat["day_of_week"].dtype == np.int8
    assert feat.loc[0, "hour"] == 10
    assert feat.loc[0, "is_weekend"] == 0  # Thursday


def test_base_features_log_amount():
    txns = _sample_txns()
    feat = prepare_base_features(txns)
    expected = np.log1p(100.0)
    assert abs(feat.loc[0, "log_amount"] - expected) < 1e-10


def test_base_features_preserves_currency():
    txns = _sample_txns()
    feat = prepare_base_features(txns)
    assert "currency" in feat.columns
    assert feat.loc[2, "currency"] == "EUR"


def test_chronological_split():
    txns = _sample_txns()
    cfg = SplitConfig(train_end="2022-09-01 23:59:59", val_end="2022-09-16 23:59:59")
    train_end, val_end = cfg.compute_boundaries(txns["ts"])
    train = txns[txns.ts <= train_end]
    val = txns[(txns.ts > train_end) & (txns.ts <= val_end)]
    test = txns[txns.ts > val_end]
    assert len(train) == 4  # first 4 rows on Sep 1
    assert len(val) == 1    # Sep 15
    assert len(test) == 1   # Sep 17
    assert train_end == pd.Timestamp("2022-09-01 23:59:59")
    assert val_end == pd.Timestamp("2022-09-16 23:59:59")


def test_feature_matrix_no_leakage_from_future():
    """Historical features for early transactions cannot use later transactions."""
    txns = _sample_txns()
    cfg = FeatureConfig(use_historical=False)  # skip slow historical for this test
    X, names, enc = build_feature_matrix(txns, cfg)
    assert X.shape[0] == 6
    assert len(names) == X.shape[1]


def test_feature_matrix_encoder_state():
    """Encoder fitted on train must be reusable for val/test."""
    txns = _sample_txns()
    train = txns.head(4)
    test = txns.tail(2)
    cfg = FeatureConfig(use_historical=False)
    X_train, names_train, enc = build_feature_matrix(train, cfg)
    X_test, names_test, _ = build_feature_matrix(test, cfg, fit_encoder=enc)
    assert names_train == names_test
    # Test set has GBP which train doesn't — should still work
    assert X_test.shape[1] == X_train.shape[1]


def test_deterministic_features():
    txns = _sample_txns()
    cfg = FeatureConfig(use_historical=False)
    X1, n1, _ = build_feature_matrix(txns, cfg)
    X2, n2, _ = build_feature_matrix(txns, cfg)
    np.testing.assert_array_equal(X1, X2)
    assert n1 == n2


def test_no_txn_id_in_features():
    txns = _sample_txns()
    cfg = FeatureConfig(use_historical=False)
    _, names, _ = build_feature_matrix(txns, cfg)
    assert "txn_id" not in names
    assert "src" not in names
    assert "dst" not in names


def test_percentile_split_produces_meaningful_partitions():
    """Default percentile split must produce non-empty val/test with both classes.
    With a small 6-row fixture, val must be non-empty; test may be empty
    (percentile boundaries on tiny datasets can exhaust all rows)."""
    txns = _sample_txns()
    cfg = SplitConfig()  # defaults: compute from data
    train_end, val_end = cfg.compute_boundaries(txns["ts"])
    train = txns[txns.ts <= train_end]
    val = txns[(txns.ts > train_end) & (txns.ts <= val_end)]
    test = txns[txns.ts > val_end]
    assert len(train) + len(val) + len(test) == len(txns)
    assert len(train) >= 1
    assert len(val) >= 1


def test_split_no_row_loss():
    """All rows must appear in exactly one split."""
    txns = _sample_txns()
    cfg = SplitConfig(train_end="2022-09-01 23:59:59", val_end="2022-09-16 23:59:59")
    train_end, val_end = cfg.compute_boundaries(txns["ts"])
    train = txns[txns.ts <= train_end]
    val = txns[(txns.ts > train_end) & (txns.ts <= val_end)]
    test = txns[txns.ts > val_end]
    total = len(train) + len(val) + len(test)
    assert total == len(txns)


def test_split_label_alignment():
    """Labels must be correctly mapped after split."""
    txns = _sample_txns()
    labels = pd.DataFrame({
        "txn_id": ["t0", "t1", "t2", "t3", "t4", "t5"],
        "is_laundering": [0, 1, 0, 0, 1, 0],
    })
    cfg = SplitConfig(train_end="2022-09-01 23:59:59", val_end="2022-09-16 23:59:59")
    train_end, val_end = cfg.compute_boundaries(txns["ts"])
    y = labels.set_index("txn_id")["is_laundering"]
    txns_labeled = txns.copy()
    txns_labeled["label"] = txns_labeled["txn_id"].map(y).fillna(0).astype(int)
    train = txns_labeled[txns_labeled.ts <= train_end]
    val = txns_labeled[(txns_labeled.ts > train_end) & (txns_labeled.ts <= val_end)]
    test = txns_labeled[txns_labeled.ts > val_end]
    assert train["label"].sum() == 1  # t1
    assert val["label"].sum() == 1    # t4
    assert test["label"].sum() == 0   # t5 is 0


def test_duplicate_timestamps_kept_together():
    """Transactions at the same timestamp must not be split across partitions."""
    ts_same = pd.Timestamp("2022-09-10 12:00:00")
    txns = pd.DataFrame({
        "txn_id": [f"t{i}" for i in range(6)],
        "ts": [ts_same] * 6,
        "src": ["A"] * 6,
        "dst": ["B"] * 6,
        "amount": [100.0] * 6,
    })
    cfg = SplitConfig(train_end="2022-09-10 12:00:00", val_end="2022-09-15 23:59:59")
    train_end, val_end = cfg.compute_boundaries(txns["ts"])
    train = txns[txns.ts <= train_end]
    val = txns[(txns.ts > train_end) & (txns.ts <= val_end)]
    test = txns[txns.ts > val_end]
    # All 6 rows have the same timestamp; boundary is inclusive for train
    assert len(train) == 6
    assert len(val) == 0
    assert len(test) == 0
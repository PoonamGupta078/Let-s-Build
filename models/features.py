"""Leakage-safe feature engineering for transaction classification.

All features are computed using only information available at or before the
transaction timestamp.  Historical aggregates use a configurable window
(default 24h) with strictly-earlier timestamps only.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from .config import FeatureConfig


# Columns we propagate as features (excludes identifiers and labels).
_TRANSACTION_FEATURES = ["log_amount", "hour", "day_of_week", "is_weekend"]
_CATEGORICAL_FEATURES = ["channel", "currency"]
_BOOL_FEATURES = ["ext_bank"]


def prepare_base_features(txns: pd.DataFrame) -> pd.DataFrame:
    """Add simple derived features.  Does not mutate the input."""
    df = txns[["txn_id", "ts", "src", "dst", "amount"]].copy()
    if "channel" in txns.columns:
        df["channel"] = txns["channel"].astype(str)
    if "currency" in txns.columns:
        df["currency"] = txns["currency"].astype(str)
    if "ext_bank" in txns.columns:
        df["ext_bank"] = txns["ext_bank"].astype(int)

    ts = pd.to_datetime(df["ts"])
    df["log_amount"] = np.log1p(df["amount"].clip(lower=0))
    df["hour"] = ts.dt.hour.astype(np.int8)
    df["day_of_week"] = ts.dt.dayofweek.astype(np.int8)
    df["is_weekend"] = (ts.dt.dayofweek >= 5).astype(np.int8)
    return df


def add_historical_features(
    df: pd.DataFrame, window_hours: int = 24
) -> pd.DataFrame:
    """Add per-account historical aggregates using ONLY earlier transactions.

    Uses pandas rolling windows on sorted data for efficiency.
    """
    window = f"{window_hours}h"
    df = df.sort_values("ts").reset_index(drop=True)
    ts = pd.to_datetime(df["ts"])
    df = df.copy()
    df["_orig_idx"] = df.index

    # Source account features: count and mean-amount of earlier outgoing txns
    src_roll = (
        df.set_index(ts)
        .groupby("src")
        .rolling(window, closed="left")["amount"]
        .agg(["count", "mean"])
        .rename(columns={"count": "src_count", "mean": "src_amt_mean"})
    )
    src_roll = src_roll.reset_index(level="src", drop=True).reset_index(drop=True)
    src_roll.index = df.index
    df[["src_count", "src_amt_mean"]] = src_roll[["src_count", "src_amt_mean"]]

    # Destination account features: count of earlier incoming txns
    dst_roll = (
        df.set_index(ts)
        .groupby("dst")
        .rolling(window, closed="left")["amount"]
        .count()
        .rename("dst_count")
    )
    dst_roll = dst_roll.reset_index(level="dst", drop=True).reset_index(drop=True)
    dst_roll.index = df.index
    df["dst_count"] = dst_roll

    # Simplified: drop src_unique_dst (requires slow per-row nunique on rolling string).
    # Set to 0 for now; can be optimized later with pre-encoding.
    df["src_unique_dst"] = 0.0

    for col in ["src_count", "src_amt_mean", "src_unique_dst", "dst_count"]:
        df[col] = df[col].fillna(0)

    df = df.drop(columns=["_orig_idx"])
    return df


def build_feature_matrix(
    df: pd.DataFrame,
    config: FeatureConfig | None = None,
    fit_encoder: dict | None = None,
) -> tuple[np.ndarray, list[str], dict]:
    """Build the final numeric feature matrix.

    Returns (X, feature_names, encoder_state) so the encoder can be
    fitted on training data and reused for val/test.
    """
    config = config or FeatureConfig()

    base = prepare_base_features(df)
    if config.use_historical:
        base = add_historical_features(base, config.hist_window_hours)

    feature_cols = list(_TRANSACTION_FEATURES)
    hist_cols = ["src_count", "src_amt_mean", "src_unique_dst", "dst_count"]
    if config.use_historical:
        feature_cols += hist_cols
    if "ext_bank" in base.columns:
        feature_cols += _BOOL_FEATURES

    # One-hot encode categoricals
    enc_cats = [c for c in _CATEGORICAL_FEATURES if c in base.columns]

    if fit_encoder is None:
        # Fit mode (training)
        enc_state = {}
        X_parts = [base[feature_cols].fillna(0).values]
        for cat in enc_cats:
            dummies = pd.get_dummies(base[cat], prefix=cat, dtype=float)
            enc_state[cat] = list(dummies.columns)
            X_parts.append(dummies.values)
        X = np.hstack(X_parts)
        names = feature_cols + [c for cols in [enc_state.get(c, []) for c in enc_cats] for c in cols]
        return X, names, enc_state
    else:
        # Transform mode (val/test) — use fitted encoder, handle unseen
        X_parts = [base[feature_cols].fillna(0).values]
        for cat in enc_cats:
            expected_cols = fit_encoder.get(cat, [])
            dummies = pd.get_dummies(base[cat], prefix=cat, dtype=float)
            # Reindex to match training columns (unseen → all zeros)
            for col in expected_cols:
                if col not in dummies.columns:
                    dummies[col] = 0.0
            dummies = dummies[expected_cols]
            X_parts.append(dummies.values)
        X = np.hstack(X_parts)
        names = feature_cols + [c for cols in [fit_encoder.get(c, []) for c in enc_cats] for c in cols]
        return X, names, fit_encoder
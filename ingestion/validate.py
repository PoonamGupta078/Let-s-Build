"""Pure transaction validation: explicit rejection reasons, never silent drops.

Rules (a row may hit several; all are reported in '_rules'):
  missing_id        txn_id, src or dst is null/blank
  bad_timestamp     ts is NaT
  bad_amount        amount is NaN or +/-inf
  negative_amount   amount < 0 (zero IS allowed: the spec requires non-negative)
  self_transfer     src == dst. Policy-controlled: the IBM data contains many
                    legitimate 'Reinvestment' self-transfers, so keep vs reject
                    is an explicit choice, never a silent drop.
  duplicate_txn_id  txn_id seen before; the FIRST occurrence is kept.

No I/O here: pure function over DataFrames so it stays trivially testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .schema import INTERNAL_TXN_COLUMNS

RULE_ORDER = [
    "missing_id", "bad_timestamp", "bad_amount",
    "negative_amount", "self_transfer", "duplicate_txn_id",
]


@dataclass(frozen=True)
class ValidationPolicy:
    """Switches that change what counts as a rejection."""

    reject_self_transfers: bool = True


@dataclass
class ValidationReport:
    """Accepted/rejected rows plus per-rule counts (AC #9: counts shown)."""

    accepted: pd.DataFrame
    rejected: pd.DataFrame  # original rows + extra '_rules' column
    counts: dict[str, int] = field(default_factory=dict)


def _blank(series: pd.Series) -> pd.Series:
    """True where a value is null, NaN or an empty/whitespace-only string."""
    s = series.astype("string").fillna("")
    return s.str.strip().eq("")


def validate_transactions(
    txns: pd.DataFrame, policy: ValidationPolicy | None = None
) -> ValidationReport:
    """Validate an internal-schema frame; never mutates the input."""
    policy = policy or ValidationPolicy()
    missing_cols = [c for c in INTERNAL_TXN_COLUMNS if c not in txns.columns]
    if missing_cols:
        raise ValueError(f"input missing internal schema columns: {missing_cols}")
    df = txns.reset_index(drop=True)

    num = pd.to_numeric(df["amount"], errors="coerce")
    blank_ids = _blank(df["txn_id"]) | _blank(df["src"]) | _blank(df["dst"])
    rules: dict[str, pd.Series] = {
        "missing_id": blank_ids,
        "bad_timestamp": pd.to_datetime(df["ts"], errors="coerce").isna(),
        "bad_amount": num.isna() | ~np.isfinite(num.fillna(np.nan)),
        "negative_amount": num < 0,
    }
    if policy.reject_self_transfers:
        same = df["src"].astype("string").fillna("") == df["dst"].astype("string").fillna("")
        rules["self_transfer"] = same & ~(_blank(df["src"]) | _blank(df["dst"]))
    else:
        rules["self_transfer"] = pd.Series(False, index=df.index)
    rules["duplicate_txn_id"] = (
        df["txn_id"].duplicated(keep="first") & ~_blank(df["txn_id"])
    )

    hit = pd.DataFrame({r: rules[r].fillna(False).astype(bool) for r in RULE_ORDER})
    any_rule = hit.any(axis=1)

    rejected_rows = df.loc[any_rule].copy()
    rejected_rows["_rules"] = hit.loc[any_rule].apply(
        lambda row: ",".join(r for r in RULE_ORDER if row[r]), axis=1
    )
    counts = {
        "total": len(df),
        "accepted": int((~any_rule).sum()),
        "rejected": int(any_rule.sum()),
    }
    counts.update({r: int(hit[r].sum()) for r in RULE_ORDER})
    return ValidationReport(
        accepted=df.loc[~any_rule].reset_index(drop=True),
        rejected=rejected_rows.reset_index(drop=True),
        counts=counts,
    )
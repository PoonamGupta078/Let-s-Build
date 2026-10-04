"""SEE orchestrator: run all detection rules on a transaction DataFrame.

Public API: ``detect(txns, config) -> list[Alert]``.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ingestion.schema import CURRENCY_COLUMN
from .models import Alert
from .rules import (
    detect_fan_in_out,
    detect_high_activity,
    detect_rapid_pass_through,
)


@dataclass(frozen=True)
class SeeConfig:
    """All thresholds for SEE detection.  Every value is configurable.

    Raises ``ValueError`` on construction if any window is non-positive
    or any threshold is less than 1.
    """

    rapid_window: pd.Timedelta = pd.Timedelta(hours=24)
    rapid_min_amount_ratio: float = 0.0
    activity_window: pd.Timedelta = pd.Timedelta(hours=24)
    activity_threshold: int = 10
    fan_window: pd.Timedelta = pd.Timedelta(hours=24)
    fan_threshold: int = 10

    def __post_init__(self) -> None:
        for name in ("rapid_window", "activity_window", "fan_window"):
            val = getattr(self, name)
            if not isinstance(val, pd.Timedelta) or val <= pd.Timedelta(0):
                raise ValueError(f"{name} must be a positive Timedelta, got {val!r}")
        for name in ("activity_threshold", "fan_threshold"):
            val = getattr(self, name)
            if not isinstance(val, int) or val < 1:
                raise ValueError(f"{name} must be >= 1, got {val!r}")
        if self.rapid_min_amount_ratio < 0:
            raise ValueError(
                f"rapid_min_amount_ratio must be >= 0, got {self.rapid_min_amount_ratio!r}"
            )


_REQUIRED_COLS = {"txn_id", "ts", "src", "dst", "amount"}


def detect(
    txns: pd.DataFrame,
    config: SeeConfig | None = None,
) -> list[Alert]:
    """Run all SEE rules on *txns* and return alerts sorted by (account, alert_id).

    Parameters
    ----------
    txns
        Validated internal-schema transactions.  Must contain the 5 core
        columns; ``currency`` is optional (rules that need it will skip
        rows where it is missing).  Rows with ``NaT`` timestamps are rejected
        with a ``ValueError``.
    config
        Threshold configuration.  Defaults are used when ``None``.

    Returns
    -------
    list[Alert]
        Alerts sorted deterministically by (account, alert_id).
    """
    config = config or SeeConfig()
    missing = _REQUIRED_COLS - set(txns.columns)
    if missing:
        raise ValueError(f"input missing required columns: {sorted(missing)}")
    if txns.empty:
        return []

    # Reject malformed timestamps explicitly rather than silently skipping.
    nat_count = int(pd.to_datetime(txns["ts"], errors="coerce").isna().sum())
    if nat_count:
        raise ValueError(
            f"input contains {nat_count} row(s) with missing or unparseable timestamps"
        )

    # Duplicate txn_ids violate the validated-input contract.
    dupes = txns["txn_id"].duplicated(keep=False)
    if dupes.any():
        dup_ids = sorted(txns.loc[dupes, "txn_id"].unique().tolist())
        raise ValueError(f"input contains duplicate txn_ids: {dup_ids[:5]}")

    has_currency = CURRENCY_COLUMN in txns.columns
    df = txns.copy()
    if not has_currency:
        df[CURRENCY_COLUMN] = "UNKNOWN"

    # Stable sort so that equal timestamps preserve their original row order.
    df = df.sort_values("ts", kind="mergesort").reset_index(drop=True)

    alerts: list[Alert] = []
    all_accounts = sorted(
        set(df["src"].astype(str).unique()) | set(df["dst"].astype(str).unique())
    )

    for acct in all_accounts:
        out_mask = df["src"].astype(str) == acct
        in_mask = df["dst"].astype(str) == acct
        out_txns = df.loc[out_mask].sort_values("ts", kind="mergesort").reset_index(drop=True)
        in_txns = df.loc[in_mask].sort_values("ts", kind="mergesort").reset_index(drop=True)

        alerts.extend(detect_rapid_pass_through(
            acct, in_txns, out_txns,
            config.rapid_window, config.rapid_min_amount_ratio,
        ))

        all_txns = pd.concat([in_txns, out_txns], ignore_index=True).sort_values(
            "ts", kind="mergesort"
        ).reset_index(drop=True)
        alerts.extend(detect_high_activity(
            acct, all_txns, config.activity_window, config.activity_threshold,
        ))

        alerts.extend(detect_fan_in_out(
            acct, in_txns, out_txns, config.fan_window, config.fan_threshold,
        ))

    alerts.sort(key=lambda a: (a.account, a.alert_id))
    return alerts

"""SEE rule implementations: rapid pass-through, high activity, fan-in/fan-out.

Each rule operates on a single-account's sorted transaction list and returns
a list[Alert].  All logic is pure: no I/O, no global state.
"""
from __future__ import annotations

import hashlib
import pandas as pd
from .models import Alert


def _alert_id(rule_id: str, account: str, evidence: tuple[str, ...]) -> str:
    """Deterministic alert id derived from rule, account, and evidence."""
    seed = f"{rule_id}|{account}|{'|'.join(evidence)}"
    return f"see-{hashlib.sha256(seed.encode()).hexdigest()[:16]}"


def _severity(score: int) -> int:
    """Clamp score to [0, 100]."""
    return max(0, min(100, int(score)))


RAPID_PASS_THROUGH_RULE_ID = "RPT001"
RAPID_PASS_THROUGH_RULE_NAME = "Rapid pass-through"
HIGH_ACTIVITY_RULE_ID = "HTA001"
HIGH_ACTIVITY_RULE_NAME = "High transaction activity"
FAN_RULE_ID = "FAN001"
FAN_RULE_NAME = "Fan-in/fan-out"


def detect_rapid_pass_through(
    account: str,
    in_txns: pd.DataFrame,
    out_txns: pd.DataFrame,
    window: pd.Timedelta,
    min_amount_ratio: float = 0.0,
) -> list[Alert]:
    """Detect rapid pass-through: funds received and sent onward within *window*.

    Incoming and outgoing transactions are matched by currency only (money is
    fungible -- we do NOT claim exact funds were traced).

    One outgoing transaction may support more than one alert if separate
    incoming transactions independently satisfy the rule within the window.
    A transaction is never paired with itself.
    """
    alerts: list[Alert] = []
    if in_txns.empty or out_txns.empty:
        return alerts

    out_by_cur: dict[str, pd.DataFrame] = {
        cur: grp.reset_index(drop=True)
        for cur, grp in out_txns.groupby("currency")
    }

    for _, in_row in in_txns.iterrows():
        cur = in_row["currency"]
        out_group = out_by_cur.get(cur)
        if out_group is None:
            continue
        t_in = in_row["ts"]
        for _, out_row in out_group.iterrows():
            dt = out_row["ts"] - t_in
            if dt < pd.Timedelta(0):
                continue
            if dt > window:
                break
            if out_row["txn_id"] == in_row["txn_id"]:
                continue
            if min_amount_ratio > 0 and in_row["amount"] > 0:
                if out_row["amount"] / in_row["amount"] < min_amount_ratio:
                    continue
            ratio = (
                out_row["amount"] / in_row["amount"]
                if in_row["amount"] > 0 else 0.0
            )
            evidence = tuple(sorted((in_row["txn_id"], out_row["txn_id"])))
            minutes = dt.total_seconds() / 60
            win_mins = max(window.total_seconds() / 60, 1)
            score = _severity(int(100 * max(0.0, 1.0 - minutes / win_mins)))
            alerts.append(Alert(
                alert_id=_alert_id(RAPID_PASS_THROUGH_RULE_ID, account, evidence),
                rule_id=RAPID_PASS_THROUGH_RULE_ID,
                rule_name=RAPID_PASS_THROUGH_RULE_NAME,
                account=account,
                score=score,
                window_start=str(t_in),
                window_end=str(out_row["ts"]),
                evidence_txn_ids=evidence,
                explanation=(
                    f"Account {account} received {in_row['amount']:.2f} {cur} "
                    f"via {in_row['txn_id']} at {t_in} and sent "
                    f"{out_row['amount']:.2f} {cur} via {out_row['txn_id']} "
                    f"at {out_row['ts']} (elapsed {minutes:.0f} min, "
                    f"ratio {ratio:.2f})."
                ),
            ))
            break  # one outgoing per incoming
    return alerts


def detect_high_activity(
    account: str,
    txns: pd.DataFrame,
    window: pd.Timedelta,
    threshold: int,
) -> list[Alert]:
    """Flag accounts whose transaction count exceeds *threshold* within *window*.

    For each transaction we count how many transactions (including itself)
    fall in [ts, ts + window].  If count >= threshold an alert is emitted.
    Only one alert per account is emitted (the first window that breaches).
    """
    if txns.empty or len(txns) < threshold:
        return []

    ts_vals = txns["ts"].to_numpy()
    txn_ids = txns["txn_id"].tolist()

    for i in range(len(ts_vals)):
        j = i
        while j < len(ts_vals) and ts_vals[j] - ts_vals[i] <= window:
            j += 1
        count = j - i
        if count >= threshold:
            evidence = tuple(txn_ids[i:j])
            score = _severity(int(100 * count / max(threshold, 1)))
            return [Alert(
                alert_id=_alert_id(HIGH_ACTIVITY_RULE_ID, account, evidence[:8]),
                rule_id=HIGH_ACTIVITY_RULE_ID,
                rule_name=HIGH_ACTIVITY_RULE_NAME,
                account=account,
                score=score,
                window_start=str(ts_vals[i]),
                window_end=str(ts_vals[j - 1]),
                evidence_txn_ids=evidence,
                explanation=(
                    f"Account {account} had {count} transactions in a "
                    f"{window.total_seconds() / 60:.0f}-min window "
                    f"(threshold {threshold})."
                ),
            )]
    return []


def detect_fan_in_out(
    account: str,
    in_txns: pd.DataFrame,
    out_txns: pd.DataFrame,
    window: pd.Timedelta,
    threshold: int,
) -> list[Alert]:
    """Flag accounts with >= *threshold* distinct counterparties in *window*.

    Counterparties are distinct src (for incoming) or dst (for outgoing)
    accounts.  Incoming and outgoing activity is intentionally combined.
    A self-transfer (A→A) appears in both directions; the merged frame is
    deduplicated on (txn_id, counterparty) to avoid double-counting rows.
    Only one alert per account.
    """
    parts: list[pd.DataFrame] = []
    if not in_txns.empty:
        tmp = in_txns[["txn_id", "ts", "src"]].rename(columns={"src": "counterparty"})
        parts.append(tmp)
    if not out_txns.empty:
        tmp = out_txns[["txn_id", "ts", "dst"]].rename(columns={"dst": "counterparty"})
        parts.append(tmp)
    if not parts:
        return []
    merged = pd.concat(parts, ignore_index=True)
    # Deduplicate: a self-transfer (A→A) appears in both in and out frames.
    # Keep one row per (txn_id, counterparty) so the row count and evidence
    # are not inflated by double-counting.
    merged = (
        merged.drop_duplicates(subset=["txn_id", "counterparty"])
        .sort_values("ts")
        .reset_index(drop=True)
    )
    if len(merged) < threshold:
        return []

    ts_vals = merged["ts"].to_numpy()
    cp_vals = merged["counterparty"].tolist()
    txn_id_vals = merged["txn_id"].tolist()

    for i in range(len(ts_vals)):
        seen: set[str] = set()
        j = i
        while j < len(ts_vals) and ts_vals[j] - ts_vals[i] <= window:
            seen.add(cp_vals[j])
            j += 1
        if len(seen) >= threshold:
            evidence = tuple(txn_id_vals[i:j])
            score = _severity(int(100 * len(seen) / max(threshold, 1)))
            return [Alert(
                alert_id=_alert_id(FAN_RULE_ID, account, evidence[:8]),
                rule_id=FAN_RULE_ID,
                rule_name=FAN_RULE_NAME,
                account=account,
                score=score,
                window_start=str(ts_vals[i]),
                window_end=str(ts_vals[j - 1]),
                evidence_txn_ids=evidence,
                explanation=(
                    f"Account {account} transacted with {len(seen)} distinct "
                    f"counterparties in a {window.total_seconds() / 60:.0f}-min "
                    f"window (threshold {threshold})."
                ),
            )]
    return []

"""TRACE: explainable, time-aware fund-flow propagation.

Wraps ``core.taint.run_taint`` with structured output, SEE alert integration,
per-currency propagation, and exit-account reporting.

Does NOT modify ``core/taint.py`` or ``core/freeze.py``.
Does NOT read from or write to Neo4j.
"""
from __future__ import annotations

import math

import pandas as pd

from core.taint import run_taint, exit_taint, top_paths
from see.models import Alert
from .config import TraceConfig
from .models import TracePath, TraceResult, TraceStep

_REQUIRED_COLS = {"txn_id", "ts", "src", "dst", "amount"}


def _validate_seed(seed_account, seed_ts, seed_amount):
    if not isinstance(seed_ts, pd.Timestamp) or pd.isna(seed_ts):
        raise ValueError(f"seed_ts must be a valid Timestamp, got {seed_ts!r}")
    if not isinstance(seed_amount, (int, float)) or not math.isfinite(seed_amount):
        raise ValueError(f"seed_amount must be finite, got {seed_amount!r}")
    if seed_amount <= 0:
        raise ValueError(f"seed_amount must be positive, got {seed_amount!r}")


def _validate_txns(txns: pd.DataFrame) -> None:
    missing = _REQUIRED_COLS - set(txns.columns)
    if missing:
        raise ValueError(f"input missing required columns: {sorted(missing)}")
    if txns.empty:
        return
    nat_count = int(pd.to_datetime(txns["ts"], errors="coerce").isna().sum())
    if nat_count:
        raise ValueError(f"input contains {nat_count} row(s) with missing or unparseable timestamps")
    dupes = txns["txn_id"].duplicated(keep=False)
    if dupes.any():
        dup_ids = sorted(txns.loc[dupes, "txn_id"].unique().tolist())
        raise ValueError(f"input contains duplicate txn_ids: {dup_ids[:5]}")
    num = pd.to_numeric(txns["amount"], errors="coerce")
    bad = num.isna() | ~num.apply(math.isfinite)
    if bad.any():
        raise ValueError(f"input contains {int(bad.sum())} row(s) with non-finite amounts")
    if (num < 0).any():
        raise ValueError(f"input contains {int((num < 0).sum())} row(s) with negative amounts")


def _resolve_seed_currency(txns, seed_account, seed_currency):
    if seed_currency is not None:
        return seed_currency
    if "currency" not in txns.columns:
        raise ValueError(
            "seed_currency not supplied and no 'currency' column in transactions. "
            "Explicitly pass seed_currency or set currency_mode='single'."
        )
    seed_rows = txns[(txns["src"] == seed_account) | (txns["dst"] == seed_account)]
    if seed_rows.empty:
        return "UNKNOWN"
    currencies = seed_rows["currency"].dropna().unique()
    if len(currencies) == 0:
        return "UNKNOWN"
    if len(currencies) > 1:
        raise ValueError(
            f"seed account {seed_account!r} appears with multiple currencies "
            f"{sorted(currencies)}; pass seed_currency explicitly."
        )
    return str(currencies[0])


def _run_per_currency(txns, seed_account, seed_ts, seed_amount, seed_currency):
    currency_txns = txns[txns["currency"] == seed_currency]
    if currency_txns.empty:
        currency_txns = txns.iloc[:0]
    return run_taint(currency_txns, {seed_account: (seed_ts, seed_amount)})


def _build_paths(taint_result, txns, config, exits):
    raw_paths = top_paths(taint_result, txns, exits, k=config.max_paths)
    paths = []
    row_map = {r.txn_id: r for r in txns.itertuples(index=False)}
    for rp in raw_paths:
        steps = []
        cur_currency = ""
        for hop in rp["hops"]:
            tid = hop["txn_id"]
            r = row_map.get(tid)
            if r is None:
                continue
            cur = getattr(r, "currency", "UNKNOWN")
            if not cur_currency:
                cur_currency = cur
            tainted_amt = hop.get("tainted", 0.0)
            txn_amount = hop.get("amount", 0.0)
            ratio = tainted_amt / txn_amount if txn_amount > 0 else 0.0
            is_first = len(steps) == 0
            reason = "seed" if is_first else f"propagated from {hop['src']}"
            steps.append(TraceStep(
                txn_id=tid, src=hop["src"], dst=hop["dst"],
                ts=hop["ts"], amount=txn_amount, currency=cur,
                tainted_amount=tainted_amt, allocation_ratio=ratio,
                reason=reason,
            ))
        if steps:
            paths.append(TracePath(
                endpoint=rp["hops"][-1]["dst"] if rp["hops"] else "",
                endpoint_tainted=rp["tainted_amount"],
                currency=cur_currency, steps=tuple(steps), greedy=True,
            ))
    return tuple(paths)


def _extract_tainted_accounts(taint_result, currency, threshold):
    result = {}
    for acct, amt in taint_result["tainted"].items():
        if abs(amt) >= threshold:
            result.setdefault(acct, {})[currency] = amt
    return result


def _extract_exit_taint(taint_result, txns, exits, currency):
    if not exits:
        return {}
    ex = txns[txns["dst"].isin(exits)]
    total = sum(taint_result["edge"].get(tid, 0.0) for tid in ex["txn_id"])
    return {currency: total} if total > 1e-9 else {}


def trace(
    txns: pd.DataFrame,
    seed_account: str,
    seed_ts: pd.Timestamp,
    seed_amount: float,
    config: TraceConfig | None = None,
    seed_currency: str | None = None,
    exits: set[str] | None = None,
) -> TraceResult:
    """Run TRACE from a single seed account.

    Parameters
    ----------
    txns : pd.DataFrame
        Validated internal-schema transactions (txn_id, ts, src, dst, amount,
        + optional currency).
    seed_account : str
        The confirmed-suspicious account.
    seed_ts : pd.Timestamp
        When the seed funds were received.  Must be valid and not NaT.
    seed_amount : float
        How much was received.  Must be finite and strictly positive.
    config : TraceConfig, optional
        Propagation configuration.  Defaults to ``TraceConfig()``.
    seed_currency : str, optional
        Currency of the seed.  Required when currency_mode="per_currency"
        and the seed account appears with multiple currencies.
    exits : set[str], optional
        Exit accounts for exit-taint reporting.

    Returns
    -------
    TraceResult
    """
    config = config or TraceConfig()
    _validate_seed(seed_account, seed_ts, seed_amount)
    _validate_txns(txns)
    df = txns.copy()

    has_currency = "currency" in df.columns
    if config.currency_mode == "per_currency" and not has_currency:
        raise ValueError(
            "currency_mode='per_currency' requires a 'currency' column in txns"
        )
    if config.currency_mode == "single":
        effective_seed_currency = seed_currency or "SINGLE_CURRENCY_ASSUMED"
    else:
        effective_seed_currency = _resolve_seed_currency(
            df, seed_account, seed_currency
        )

    if config.currency_mode == "per_currency" and has_currency:
        taint_result = _run_per_currency(
            df, seed_account, seed_ts, seed_amount, effective_seed_currency
        )
    else:
        taint_result = run_taint(
            df, {seed_account: (seed_ts, seed_amount)}
        )

    cur_label = effective_seed_currency if has_currency else "UNKNOWN"
    tainted_accounts = _extract_tainted_accounts(
        taint_result, cur_label, config.min_tainted_threshold
    )
    tainted_edges = {
        tid: amt for tid, amt in taint_result["edge"].items()
        if abs(amt) >= config.min_tainted_threshold
    }
    exit_taint_map = _extract_exit_taint(
        taint_result, df, exits or set(), cur_label
    )
    paths = _build_paths(taint_result, df, config, exits) if exits else ()

    config_dict = {
        "currency_mode": config.currency_mode,
        "max_paths": config.max_paths,
        "min_tainted_threshold": config.min_tainted_threshold,
    }
    if config.currency_mode == "single":
        config_dict["single_currency_assumption"] = (
            "Caller asserted all amounts share one currency."
        )

    return TraceResult(
        alert_id="", seed_account=seed_account, seed_amount=seed_amount,
        seed_currency=effective_seed_currency, seed_ts=str(seed_ts),
        config=config_dict, tainted_accounts=tainted_accounts,
        tainted_edges=tainted_edges, exit_taint_by_currency=exit_taint_map,
        paths=paths,
    )


def trace_from_alert(
    txns: pd.DataFrame, alert: Alert, seed_ts: pd.Timestamp,
    seed_amount: float, config: TraceConfig | None = None,
    seed_currency: str | None = None, exits: set[str] | None = None,
) -> TraceResult:
    """Derive seed from a SEE alert and run TRACE.

    The caller must supply seed_ts and seed_amount — these are not
    inferred from the alert's score or evidence.
    """
    result = trace(
        txns, alert.account, seed_ts, seed_amount,
        config=config, seed_currency=seed_currency, exits=exits,
    )
    return TraceResult(
        alert_id=alert.alert_id, seed_account=result.seed_account,
        seed_amount=result.seed_amount, seed_currency=result.seed_currency,
        seed_ts=result.seed_ts, config=result.config,
        tainted_accounts=result.tainted_accounts,
        tainted_edges=result.tainted_edges,
        exit_taint_by_currency=result.exit_taint_by_currency,
        paths=result.paths, disclaimer=result.disclaimer,
    )
 

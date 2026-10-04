"""TRACE: explainable, time-aware fund-flow propagation.

Wraps core.taint.run_taint with structured output, SEE alert integration,
and per-currency propagation.  Does NOT modify core/taint.py or core/freeze.py.
"""
from __future__ import annotations

import pandas as pd

from core.taint import run_taint, top_paths
from see.models import Alert
from .config import TraceConfig
from .models import TracePath, TraceResult, TraceStep

_REQUIRED_COLS = {"txn_id", "ts", "src", "dst", "amount"}


def _build_paths(taint_result: dict, txns: pd.DataFrame,
                 config: TraceConfig) -> tuple[TracePath, ...]:
    """Build structured TracePath objects from core.taint results."""
    raw_paths = top_paths(taint_result, txns, set(), k=config.max_paths)
    paths: list[TracePath] = []
    row_map = {r.txn_id: r for r in txns.itertuples(index=False)}

    for rp in raw_paths:
        steps: list[TraceStep] = []
        cur_currency = ""
        for hop in rp["hops"]:
            tid = hop["txn_id"]
            r = row_map.get(tid)
            if r is None:
                continue
            cur = getattr(r, "currency", "UNKNOWN")
            if not cur_currency:
                cur_currency = cur
            # First hop in a path is the seed; rest are propagated.
            is_first = len(steps) == 0
            reason = "seed" if is_first else f"propagated from {hop['src']}"
            steps.append(TraceStep(
                txn_id=tid, src=hop["src"], dst=hop["dst"],
                ts=hop["ts"], amount=hop["amount"], currency=cur,
                tainted_amount=hop.get("tainted", 0.0),
                allocation_ratio=0.0,
                reason=reason,
            ))
        if steps:
            paths.append(TracePath(
                endpoint=rp["hops"][-1]["dst"] if rp["hops"] else "",
                endpoint_tainted=rp["tainted_amount"],
                currency=cur_currency,
                steps=tuple(steps),
            ))
    return tuple(paths)


def trace(
    txns: pd.DataFrame,
    seed_account: str,
    seed_ts: pd.Timestamp,
    seed_amount: float,
    config: TraceConfig | None = None,
    alert_id: str = "",
) -> TraceResult:
    """Run TRACE from a single seed account.

    Parameters
    ----------
    txns : validated internal-schema DataFrame
    seed_account : confirmed-suspicious account
    seed_ts : when seed funds were received
    seed_amount : how much was received
    config : optional TraceConfig
    alert_id : optional source alert ID

    Returns
    -------
    TraceResult with tainted accounts, edges, and provenance paths.
    """
    config = config or TraceConfig()
    missing = _REQUIRED_COLS - set(txns.columns)
    if missing:
        raise ValueError(f"input missing required columns: {sorted(missing)}")

    if seed_amount <= 0:
        raise ValueError(f"seed_amount must be positive, got {seed_amount}")

    has_currency = "currency" in txns.columns

    # Determine seed currency
    seed_currency = "UNKNOWN"
    if has_currency:
        seed_cur_rows = txns[
            (txns["src"] == seed_account) | (txns["dst"] == seed_account)
        ]
        if not seed_cur_rows.empty:
            seed_currency = str(seed_cur_rows["currency"].iloc[0])

    # Per-currency mode: propagate only within seed's currency
    if config.currency_mode == "per_currency" and has_currency:
        currency_txns = txns[txns["currency"] == seed_currency]
        if currency_txns.empty:
            currency_txns = txns.iloc[:0]  # empty frame with same columns
        taint_result = run_taint(
            currency_txns, {seed_account: (seed_ts, seed_amount)}
        )
    else:
        # Single mode: all currencies fungible
        taint_result = run_taint(
            txns, {seed_account: (seed_ts, seed_amount)}
        )

    # Extract results
    tainted_accounts: dict[str, float] = {}
    for acct, amt in taint_result["tainted"].items():
        if abs(amt) >= config.min_tainted_threshold:
            tainted_accounts[acct] = amt

    tainted_edges: dict[str, float] = {}
    for tid, amt in taint_result["edge"].items():
        if abs(amt) >= config.min_tainted_threshold:
            tainted_edges[tid] = amt

    paths = _build_paths(taint_result, txns, config)

    return TraceResult(
        alert_id=alert_id,
        seed_account=seed_account,
        seed_amount=seed_amount,
        seed_currency=seed_currency,
        seed_ts=str(seed_ts),
        config={
            "currency_mode": config.currency_mode,
            "max_paths": config.max_paths,
            "min_tainted_threshold": config.min_tainted_threshold,
        },
        tainted_accounts=tainted_accounts,
        tainted_edges=tainted_edges,
        paths=paths,
    )


def trace_from_alert(
    txns: pd.DataFrame,
    alert: Alert,
    seed_ts: pd.Timestamp,
    seed_amount: float,
    config: TraceConfig | None = None,
) -> TraceResult:
    """Derive seed from a SEE alert and run TRACE."""
    return trace(
        txns, alert.account, seed_ts, seed_amount,
        config=config, alert_id=alert.alert_id,
    )
 

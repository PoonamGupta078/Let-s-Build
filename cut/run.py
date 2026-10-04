"""CUT: advisory intervention recommendation engine.

Wraps ``core.freeze.plan`` and ``core.freeze.block_all`` with structured
output, currency isolation, and SEE/TRACE integration.

Does NOT modify ``core/freeze.py`` or ``core/taint.py``.
Does NOT execute holds or write to any database.
"""
from __future__ import annotations

import math

import pandas as pd

from core.freeze import plan, block_all
from core.taint import run_taint, exit_taint
from trace.models import TraceResult
from .config import CutConfig
from .models import CutRecommendation, CutResult

_REQUIRED_COLS = {"txn_id", "ts", "src", "dst", "amount"}


def _validate_inputs(txns, seeds, exits, t_alert):
    missing = _REQUIRED_COLS - set(txns.columns)
    if missing:
        raise ValueError(f"input missing required columns: {sorted(missing)}")
    if not seeds:
        raise ValueError("seeds must be a non-empty dict")
    if not exits:
        raise ValueError("exits must be a non-empty set")
    if not isinstance(t_alert, pd.Timestamp) or pd.isna(t_alert):
        raise ValueError(f"t_alert must be a valid Timestamp, got {t_alert!r}")
    for acct, (ts, amt) in seeds.items():
        if not isinstance(ts, pd.Timestamp) or pd.isna(ts):
            raise ValueError(f"seed {acct!r} has invalid timestamp: {ts!r}")
        if not isinstance(amt, (int, float)) or not math.isfinite(amt):
            raise ValueError(f"seed {acct!r} has non-finite amount: {amt!r}")
        if amt <= 0:
            raise ValueError(f"seed {acct!r} has non-positive amount: {amt!r}")
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


def _get_evidence(taint_result, account, threshold):
    """Get evidence txn_ids for an account from taint result parents."""
    evidence = []
    if "parents" in taint_result and account in taint_result["parents"]:
        for txn_id, _src, tainted_amt in taint_result["parents"][account]:
            if tainted_amt >= threshold:
                evidence.append(txn_id)
    return tuple(sorted(set(evidence)))


def _build_rationale(account, rank, total_ranks, tainted_blocked,
                     clean_disrupted, eta, strategy):
    parts = [f"Blocking account {account}"]
    if tainted_blocked is not None and tainted_blocked > 0:
        parts.append(f"is estimated to intercept {tainted_blocked:,.0f} in tainted funds")
    if clean_disrupted is not None and clean_disrupted > 0:
        parts.append(f"while disrupting {clean_disrupted:,.0f} in clean transaction volume")
    if eta is not None:
        parts.append(f"(next tainted exit in {eta:.0f} minutes)")
    if strategy == "greedy" and rank is not None and total_ranks is not None:
        parts.append(f"Greedy rank {rank} of {total_ranks} — approximation, not globally optimal.")
    elif strategy == "block_all":
        parts.append("Minimum cut-set strategy (unranked).")
    return " ".join(parts) + "."


def _config_dict(config, seed_currency):
    return {
        "strategy": config.strategy, "max_recommendations": config.max_recommendations,
        "hold_cost": config.hold_cost, "min_tainted_gain": config.min_tainted_gain,
        "block_all_hold_cost": config.block_all_hold_cost,
        "min_tainted_threshold": config.min_tainted_threshold,
        "seed_currency": seed_currency,
    }


def _greedy(txns, seeds, exits, t_alert, config, seed_currency):
    result = plan(
        txns, seeds, exits, t_alert,
        k=config.max_recommendations, hold_cost=config.hold_cost,
        min_gain=config.min_tainted_gain,
    )
    holds = result["holds"]
    if not holds:
        return CutResult(
            strategy="greedy", seed_accounts=tuple(sorted(seeds.keys())),
            exit_accounts=tuple(sorted(exits)), baseline_exit_taint=0.0,
            total_tainted_blocked=0.0, pct_blocked=0.0, recommendations=(),
            config=_config_dict(config, seed_currency),
        )
    taint_result = run_taint(txns, seeds)
    total_ranks = len(holds)
    recs = []
    for i, h in enumerate(holds):
        evidence = _get_evidence(taint_result, h["account"], config.min_tainted_threshold)
        eta = h.get("minutes_until_exit")
        rationale = _build_rationale(
            h["account"], i + 1, total_ranks, h["tainted_blocked"],
            h["clean_held"], eta, "greedy",
        )
        recs.append(CutRecommendation(
            account=h["account"], rank=i + 1, strategy="greedy",
            evidence_txn_ids=evidence,
            estimated_tainted_blocked=h["tainted_blocked"],
            estimated_clean_disrupted=h["clean_held"],
            minutes_until_exit=eta, rationale=rationale, currency=seed_currency,
        ))
    baseline = result["baseline_exit_taint"]
    pct = 100.0 * result["blocked_total"] / baseline if baseline > 0 else 0.0
    return CutResult(
        strategy="greedy", seed_accounts=tuple(sorted(seeds.keys())),
        exit_accounts=tuple(sorted(exits)), baseline_exit_taint=baseline,
        total_tainted_blocked=result["blocked_total"], pct_blocked=pct,
        recommendations=tuple(recs), config=_config_dict(config, seed_currency),
    )


def _block_all_strategy(txns, seeds, exits, t_alert, config, seed_currency):
    result = block_all(txns, seeds, exits, t_alert, hold_cost=config.block_all_hold_cost)
    holds = result.get("holds", [])
    if not holds:
        return CutResult(
            strategy="block_all", seed_accounts=tuple(sorted(seeds.keys())),
            exit_accounts=tuple(sorted(exits)), baseline_exit_taint=0.0,
            total_tainted_blocked=0.0, pct_blocked=0.0, recommendations=(),
            config=_config_dict(config, seed_currency),
        )
    base = run_taint(txns, seeds)
    baseline = exit_taint(base, txns, exits)
    recs = []
    for acct in holds:
        rationale = _build_rationale(acct, None, None, None, None, None, "block_all")
        recs.append(CutRecommendation(
            account=acct, rank=None, strategy="block_all",
            evidence_txn_ids=(), estimated_tainted_blocked=None,
            estimated_clean_disrupted=None, minutes_until_exit=None,
            rationale=rationale, currency=seed_currency,
        ))
    aggregate_clean = result.get("clean_held", None)
    return CutResult(
        strategy="block_all", seed_accounts=tuple(sorted(seeds.keys())),
        exit_accounts=tuple(sorted(exits)), baseline_exit_taint=baseline,
        total_tainted_blocked=0.0, pct_blocked=None,
        recommendations=tuple(recs), config=_config_dict(config, seed_currency),
        aggregate_clean_held=aggregate_clean,
    )


def recommend(
    txns: pd.DataFrame,
    seeds: dict[str, tuple[pd.Timestamp, float]],
    exits: set[str],
    t_alert: pd.Timestamp,
    config: CutConfig | None = None,
    seed_currency: str | None = None,
) -> CutResult:
    """Run CUT recommendation engine.

    Parameters
    ----------
    txns : pd.DataFrame
        Validated internal-schema transactions.
    seeds : dict
        Seed accounts: {account: (timestamp, amount)}.
    exits : set[str]
        Exit accounts.
    t_alert : pd.Timestamp
        Alert timestamp.
    config : CutConfig, optional
        Recommendation configuration.
    seed_currency : str, optional
        Currency label for recommendations.

    Returns
    -------
    CutResult
        Advisory recommendations.  No holds are executed.
    """
    config = config or CutConfig()
    _validate_inputs(txns, seeds, exits, t_alert)
    df = txns.copy()
    effective_currency = seed_currency or "UNKNOWN"
    if config.strategy == "greedy":
        return _greedy(df, seeds, exits, t_alert, config, effective_currency)
    else:
        return _block_all_strategy(df, seeds, exits, t_alert, config, effective_currency)


def recommend_from_trace(
    txns: pd.DataFrame,
    trace_result: TraceResult,
    exits: set[str],
    t_alert: pd.Timestamp,
    config: CutConfig | None = None,
) -> CutResult:
    """Extract seed from a TraceResult and run CUT.

    Uses ``trace_result.seed_account``, ``seed_amount``, ``seed_ts``,
    and ``seed_currency`` directly.  Does NOT infer seed amount from
    alert score or unrelated evidence.
    """
    seed_ts = pd.Timestamp(trace_result.seed_ts)
    seeds = {trace_result.seed_account: (seed_ts, trace_result.seed_amount)}
    return recommend(
        txns, seeds, exits, t_alert,
        config=config, seed_currency=trace_result.seed_currency,
    )
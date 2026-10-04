"""One-command synthetic demo: SEE -> TRACE -> CUT.

Usage: python scripts/run_demo.py

Runs the verified synthetic workflow on a deterministic seeded case
(S -> M1/M2 -> CASH) with no background noise.  Requires no Neo4j, no API
server, no frontend dependencies, no credentials, and no full dataset.

Output is advisory only: fund propagation is ESTIMATED (money is fungible)
and no account is actually frozen.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.make_case import make_case  # noqa: E402
from see.run import detect  # noqa: E402
from trace.config import TraceConfig  # noqa: E402
from trace.run import trace  # noqa: E402
from cut.run import recommend  # noqa: E402


def _money(value) -> str:
    """Format a monetary value, tolerating None."""
    if value is None:
        return "n/a"
    return f"{value:,.2f}"


def main() -> int:
    # 1. Build the deterministic case (no background noise).
    case = make_case(seed=42, background_rows=0)
    txns = case.transactions
    print("=" * 70)
    print("SecureTrace synthetic demo: SEE -> TRACE -> CUT")
    print("=" * 70)
    print("\nCase: synthetic, currency-agnostic (no 'currency' column).")
    print(f"Transactions: {len(txns)}")
    print(f"Seed(s): {sorted(case.seeds)}   Exit(s): {sorted(case.exits)}")
    for row in txns.itertuples(index=False):
        print(f"  {row.txn_id:9s} {str(row.ts)[11:16]}  "
              f"{row.src:>5s} -> {row.dst:>5s}  {row.amount:,.0f}")

    # 2. SEE: suspicious-activity detection.
    print("\n--- SEE: suspicious-activity detection ---")
    alerts = detect(txns)
    if not alerts:
        print("  (no alerts produced)")
    for alert in alerts:
        print(f"  [{alert.rule_id}] {alert.rule_name} - account {alert.account}, "
              f"score {alert.score}")
        print(f"      alert_id: {alert.alert_id}")
        print(f"      evidence: {list(alert.evidence_txn_ids)}")
        print(f"      explanation: {alert.explanation}")

    # 3. TRACE: estimated fund propagation.
    seed_account, (seed_ts, seed_amount) = next(iter(case.seeds.items()))
    print("\n--- TRACE: estimated fund propagation ---")
    print(f"  seed: {seed_account} @ {seed_ts}  amount {_money(seed_amount)}")
    trace_result = trace(
        txns, seed_account, seed_ts, seed_amount,
        config=TraceConfig(currency_mode="single"),  # case has no currency column
        exits=case.exits,
    )
    print("  estimated tainted accounts:")
    for acct in sorted(trace_result.tainted_accounts):
        for currency, amount in sorted(trace_result.tainted_accounts[acct].items()):
            print(f"    {acct}: {_money(amount)} {currency}")
    if trace_result.exit_taint_by_currency:
        print("  estimated tainted reaching exits:")
        for currency, amount in sorted(trace_result.exit_taint_by_currency.items()):
            print(f"    {currency}: {_money(amount)}")
    if trace_result.paths:
        print(f"  provenance paths ({len(trace_result.paths)}):")
        for path in trace_result.paths:
            route = " -> ".join(step.dst for step in path.steps)
            print(f"    {seed_account} -> {route}  (tainted {_money(path.endpoint_tainted)})")

    # 4. CUT: advisory intervention recommendations.
    t_alert = seed_ts + pd.Timedelta(minutes=20)
    print("\n--- CUT: advisory intervention recommendations ---")
    print(f"  alert time: {t_alert}")
    cut_result = recommend(txns, case.seeds, case.exits, t_alert)
    print(f"  strategy: {cut_result.strategy}")
    if cut_result.pct_blocked is not None:
        print(f"  estimated blocked taint: {cut_result.pct_blocked:.1f}%")
    for rec in cut_result.recommendations:
        rank = rec.rank if rec.rank is not None else "-"
        print(f"  #{rank} account {rec.account}:")
        if rec.estimated_tainted_blocked is not None:
            print(f"      estimated tainted blocked: {_money(rec.estimated_tainted_blocked)}")
        if rec.estimated_clean_disrupted is not None:
            print(f"      estimated clean disrupted: {_money(rec.estimated_clean_disrupted)}")
        if rec.minutes_until_exit is not None:
            print(f"      minutes until exit: {rec.minutes_until_exit:.0f}")
        print(f"      rationale: {rec.rationale}")

    # 5. Disclaimer.
    print("\n" + "=" * 70)
    print("DISCLAIMER")
    print("=" * 70)
    print("Fund propagation is ESTIMATED; money is fungible, so these are")
    print("accounting-policy estimates, not proof that specific physical funds")
    print("moved or that any account committed a crime.")
    print("Recommendations are ADVISORY ONLY. No account has been frozen;")
    print("a human investigator makes the final decision.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

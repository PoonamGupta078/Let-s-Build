"""TRACE tests: 25 required cases + CUT regression."""
import math
import pandas as pd
import pytest

from trace.config import TraceConfig
from trace.models import TraceResult
from trace.run import trace, trace_from_alert
from see.models import Alert
from core.taint import run_taint
from core.freeze import plan

T0 = pd.Timestamp("2022-09-01 10:00")
_m = pd.Timedelta


def _txns(rows):
    return pd.DataFrame(rows, columns=["txn_id", "ts", "src", "dst", "amount", "currency"])


def _alert(account):
    return Alert(alert_id="see-test", rule_id="RPT001", rule_name="Rapid pass-through",
                 account=account, score=100, window_start=str(T0), window_end=str(T0 + _m(hours=1)),
                 evidence_txn_ids=("t1",), explanation="test")


# 1. single seed + one outgoing
def test_01_single_seed_one_outgoing():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert r.tainted_accounts["B"]["USD"] == pytest.approx(600.0)
    assert r.tainted_edges["t1"] == pytest.approx(600.0)

# 2. partial taint ratio
def test_02_partial_taint_ratio():
    txns = _txns([("c", T0, "X", "A", 500.0, "USD"), ("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    r = trace(txns, "A", T0, 500.0, seed_currency="USD")
    assert r.tainted_accounts["B"]["USD"] == pytest.approx(300.0)

# 3. multiple incoming
def test_03_multiple_incoming():
    txns = _txns([("c", T0, "X", "A", 700.0, "USD"), ("t1", T0 + _m(minutes=10), "A", "B", 500.0, "USD")])
    r = trace(txns, "A", T0, 300.0, seed_currency="USD")
    assert r.tainted_accounts["B"]["USD"] == pytest.approx(150.0)

# 4. multiple outgoing no double-count
def test_04_multiple_outgoing_no_double_count():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 400.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "A", "C", 400.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert sum(r.tainted_edges.values()) <= 1000.0 + 1e-6
    assert r.tainted_accounts["B"]["USD"] == pytest.approx(400.0)

# 5. three currencies independent
def test_05_three_currencies_independent():
    txns = _txns([("u1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
                  ("e1", T0 + _m(minutes=20), "A", "C", 500.0, "EUR"),
                  ("g1", T0 + _m(minutes=30), "A", "D", 400.0, "GBP")])
    r = trace(txns, "A", T0, 1000.0, config=TraceConfig(currency_mode="per_currency"), seed_currency="USD")
    assert r.tainted_accounts["B"]["USD"] == pytest.approx(600.0)
    assert "C" not in r.tainted_accounts
    assert "D" not in r.tainted_accounts

# 6. missing/ambiguous seed currency
def test_06_ambiguous_seed_currency_raises():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 100.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "A", "C", 100.0, "EUR")])
    with pytest.raises(ValueError, match="multiple currencies"):
        trace(txns, "A", T0, 1000.0)

def test_per_currency_without_currency_column_raises():
    """per_currency mode requires a currency column even when seed_currency is supplied."""
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 100.0, "USD")])
    txns = txns.drop(columns=["currency"])
    cfg = TraceConfig(currency_mode="per_currency")
    with pytest.raises(ValueError, match="requires a 'currency' column"):
        trace(txns, "A", T0, 1000.0, config=cfg, seed_currency="USD")

# 7. invalid currency mode
def test_07_invalid_currency_mode():
    with pytest.raises(ValueError, match="currency_mode"):
        TraceConfig(currency_mode="invalid")

# 8. out-of-order timestamps
def test_08_out_of_order_not_traced():
    txns = _txns([("t1", T0, "B", "C", 100.0, "USD"), ("t2", T0 + _m(minutes=30), "A", "B", 100.0, "USD")])
    r = trace(txns, "A", T0 + _m(minutes=10), 100.0, seed_currency="USD")
    assert "C" not in r.tainted_accounts

# 9. equal-timestamp determinism
def test_09_equal_timestamp_determinism():
    txns = _txns([("t1", T0, "A", "B", 100.0, "USD"), ("t2", T0, "A", "C", 200.0, "USD")])
    r1 = trace(txns, "A", T0, 500.0, seed_currency="USD")
    r2 = trace(txns, "A", T0, 500.0, seed_currency="USD")
    assert r1.to_json() == r2.to_json()

# 10. cycles
def test_10_cycle_converges():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 500.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "B", "C", 500.0, "USD"),
                  ("t3", T0 + _m(minutes=30), "C", "A", 500.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    total_tainted = sum(v for amt in r.tainted_accounts.values() for v in amt.values())
    for amt in r.tainted_accounts.values():
        for v in amt.values():
            assert v >= 0 and v < float("inf")
    assert total_tainted <= 1000.0 + 1e-6

# 11. self-transfers
def test_11_self_transfer_preserves_taint():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "A", 500.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert r.tainted_accounts["A"]["USD"] == pytest.approx(1000.0)


# 12. missing required columns
def test_12_missing_required_columns_raises():
    with pytest.raises(ValueError, match="missing required columns"):
        trace(pd.DataFrame({"txn_id": ["t1"]}), "A", T0, 1000.0)

# 13. NaT timestamps
def test_13_nat_timestamp_raises():
    txns = pd.DataFrame({"txn_id": ["t1"], "ts": [pd.NaT], "src": ["A"],
                         "dst": ["B"], "amount": [100.0], "currency": ["USD"]})
    with pytest.raises(ValueError, match="unparseable timestamps"):
        trace(txns, "A", T0, 1000.0)

# 14. non-finite and negative amounts
def test_14a_nonfinite_amount_raises():
    txns = _txns([("t1", T0, "A", "B", float("nan"), "USD")])
    with pytest.raises(ValueError, match="non-finite"):
        trace(txns, "A", T0, 1000.0)

def test_14b_negative_amount_raises():
    txns = _txns([("t1", T0, "A", "B", -100.0, "USD")])
    with pytest.raises(ValueError, match="negative"):
        trace(txns, "A", T0, 1000.0)

# 15. duplicate transaction IDs
def test_15_duplicate_txn_ids_raises():
    txns = _txns([("dup", T0, "A", "B", 100.0, "USD"),
                  ("dup", T0 + _m(minutes=10), "B", "C", 50.0, "USD")])
    with pytest.raises(ValueError, match="duplicate"):
        trace(txns, "A", T0, 1000.0)

# 16. empty transaction input
def test_16_empty_transactions():
    r = trace(_txns([]), "A", T0, 1000.0, seed_currency="USD")
    assert isinstance(r, TraceResult)
    assert r.tainted_edges == {}
    assert r.tainted_accounts["A"]["USD"] == pytest.approx(1000.0)

# 17. zero-amount transaction
def test_17_zero_amount_transaction():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 0.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert r.tainted_edges.get("t1", 0.0) == pytest.approx(0.0)

# 18. input immutability
def test_18_input_immutability():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    snap = txns.copy(deep=True)
    trace(txns, "A", T0, 1000.0, seed_currency="USD")
    pd.testing.assert_frame_equal(txns, snap)

# 19. deterministic serialization
def test_19_deterministic_serialization():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    r1 = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    r2 = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert r1.to_json() == r2.to_json()
    assert "tainted_accounts" in r1.to_dict()

# 20. provenance path contents
def test_20_provenance_path_contents():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "B", "D", 300.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD", exits={"D"})
    assert len(r.paths) > 0
    p = r.paths[0]
    assert p.endpoint_tainted > 0
    assert p.steps[0].reason == "seed"
    if len(p.steps) > 1:
        assert "propagated from" in p.steps[1].reason


# 21. greedy-path labeling
def test_21_greedy_path_labeling():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "B", "D", 300.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD", exits={"D"})
    if r.paths:
        assert r.paths[0].greedy is True

# 22. SEE alert adapter
def test_22_see_alert_adapter():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    alert = _alert("A")
    r = trace_from_alert(txns, alert, T0, 1000.0, seed_currency="USD")
    assert r.alert_id == "see-test"
    assert r.seed_account == "A"
    r_manual = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert r.tainted_accounts == r_manual.tainted_accounts

# 23. invalid seed amount and timestamp
def test_23a_invalid_seed_amount():
    txns = _txns([("t1", T0, "A", "B", 100.0, "USD")])
    with pytest.raises(ValueError, match="positive"):
        trace(txns, "A", T0, -100.0)
    with pytest.raises(ValueError, match="positive"):
        trace(txns, "A", T0, 0.0)
    with pytest.raises(ValueError, match="finite"):
        trace(txns, "A", T0, float("inf"))

def test_23b_invalid_seed_timestamp():
    txns = _txns([("t1", T0, "A", "B", 100.0, "USD")])
    with pytest.raises(ValueError, match="valid Timestamp"):
        trace(txns, "A", pd.NaT, 1000.0)

# 24. insufficient-balance haircut
def test_24_insufficient_balance_haircut():
    """A receives 1000 seed, sends 600 to B, then 500 to C.
    After first: tainted[A]=400, balance[A]=400.
    Second: eff=max(400,500)=500, ratio=400/500=0.8, tainted=400."""
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "A", "C", 500.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD")
    assert r.tainted_accounts["C"]["USD"] == pytest.approx(400.0)
    assert r.tainted_edges["t2"] <= 500.0 + 1e-6

# 25. currency-specific exit reporting
def test_25_exit_taint_by_currency():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
                  ("t2", T0 + _m(minutes=20), "B", "EXIT", 300.0, "USD")])
    r = trace(txns, "A", T0, 1000.0, seed_currency="USD", exits={"EXIT"})
    assert "USD" in r.exit_taint_by_currency
    assert r.exit_taint_by_currency["USD"] > 0


# --- CUT regression ---


def test_cut_regression_unchanged():
    """Verify core.taint and core.freeze still work identically."""
    RING = pd.DataFrame(
        [("s1", T0 + _m(minutes=10), "S", "M1", 500000.0),
         ("s2", T0 + _m(minutes=10), "S", "M2", 500000.0),
         ("e1", T0 + _m(minutes=40), "M1", "CASH", 500000.0),
         ("e2", T0 + _m(minutes=40), "M2", "CASH", 500000.0)],
        columns=["txn_id", "ts", "src", "dst", "amount"],
    )
    seeds = {"S": (T0, 1_000_000.0)}
    r = run_taint(RING, seeds)
    p = plan(RING, seeds, {"CASH"}, t_alert=T0 + _m(minutes=20), k=2)
    assert p["pct_blocked"] > 99
    assert len(p["holds"]) == 2
 

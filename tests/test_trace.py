"""TRACE tests: time-respecting haircut taint propagation with SEE integration.

All tests use small synthetic fixtures; never loads the full IBM dataset.
"""
import pandas as pd
import pytest

from trace.config import TraceConfig
from trace.models import TraceResult
from trace.run import trace, trace_from_alert
from see.models import Alert

T0 = pd.Timestamp("2022-09-01 10:00")
_m = pd.Timedelta


def _txns(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=["txn_id", "ts", "src", "dst", "amount", "currency"],
    )


def _alert(account: str) -> Alert:
    return Alert(
        alert_id="see-test", rule_id="RPT001", rule_name="Rapid pass-through",
        account=account, score=100,
        window_start=str(T0), window_end=str(T0 + _m(hours=1)),
        evidence_txn_ids=("t1",), explanation="test",
    )


# --- core propagation ---


def test_single_in_single_out():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    result = trace(txns, "A", T0, 1000.0)
    assert isinstance(result, TraceResult)
    assert result.tainted_accounts.get("B", 0) == pytest.approx(600.0)
    assert result.tainted_edges["t1"] == pytest.approx(600.0)


def test_partial_propagation():
    txns = _txns([
        ("clean", T0, "X", "A", 500.0, "USD"),
        ("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
    ])
    result = trace(txns, "A", T0, 500.0)
    assert result.tainted_accounts.get("B", 0) == pytest.approx(300.0)


def test_multiple_incoming():
    txns = _txns([
        ("clean", T0, "X", "A", 700.0, "USD"),
        ("t1", T0 + _m(minutes=10), "A", "B", 500.0, "USD"),
    ])
    result = trace(txns, "A", T0, 300.0)
    assert result.tainted_accounts.get("B", 0) == pytest.approx(150.0)


def test_multiple_outgoing_no_double_count():
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "B", 400.0, "USD"),
        ("t2", T0 + _m(minutes=20), "A", "C", 400.0, "USD"),
    ])
    result = trace(txns, "A", T0, 1000.0)
    total_out = sum(result.tainted_edges.values())
    assert total_out <= 1000.0 + 1e-6
    assert result.tainted_accounts.get("B", 0) == pytest.approx(400.0)
    assert result.tainted_accounts.get("C", 0) == pytest.approx(400.0)


# --- currency ---


def test_different_currencies_per_currency_mode():
    """Seed in USD; EUR txns get zero taint in per_currency mode."""
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
        ("t2", T0 + _m(minutes=20), "A", "C", 500.0, "EUR"),
    ])
    cfg = TraceConfig(currency_mode="per_currency")
    result = trace(txns, "A", T0, 1000.0, config=cfg)
    assert result.tainted_accounts.get("B", 0) == pytest.approx(600.0)
    assert result.tainted_accounts.get("C", 0) == pytest.approx(0.0)


def test_single_currency_mode_treats_all_as_fungible():
    """In single mode, EUR txns DO receive taint from USD seed.
    After A sends 600 to B, tainted[A]=400. Sending 500 to C with ratio
    400/500=0.8 gives tainted[C]=400 (haircut on insufficient balance)."""
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
        ("t2", T0 + _m(minutes=20), "A", "C", 500.0, "EUR"),
    ])
    cfg = TraceConfig(currency_mode="single")
    result = trace(txns, "A", T0, 1000.0, config=cfg)
    assert result.tainted_accounts.get("B", 0) == pytest.approx(600.0)
    assert result.tainted_accounts.get("C", 0) == pytest.approx(400.0)  # haircut


# --- time ordering ---


def test_out_of_order_not_traced():
    """B→C before seed. Tainted[C] must be zero."""
    txns = _txns([
        ("t1", T0, "B", "C", 100.0, "USD"),          # before seed
        ("t2", T0 + _m(minutes=30), "A", "B", 100.0, "USD"),
    ])
    result = trace(txns, "A", T0 + _m(minutes=10), 100.0)
    assert result.tainted_accounts.get("C", 0) == pytest.approx(0.0)


# --- cycles and self-transfers ---


def test_cycle_converges():
    """A→B→C→A cycle. Tainted decreases each loop; no infinite loop."""
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "B", 500.0, "USD"),
        ("t2", T0 + _m(minutes=20), "B", "C", 500.0, "USD"),
        ("t3", T0 + _m(minutes=30), "C", "A", 500.0, "USD"),
    ])
    result = trace(txns, "A", T0, 1000.0)
    # Tainted must be finite and non-negative
    for acct, amt in result.tainted_accounts.items():
        assert amt >= 0
        assert amt < float("inf")


def test_self_transfer_preserves_taint():
    """A→A self-transfer. Tainted on A unchanged."""
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "A", 500.0, "USD"),
    ])
    result = trace(txns, "A", T0, 1000.0)
    # After self-transfer, tainted[A] should still be 1000
    assert result.tainted_accounts.get("A", 0) == pytest.approx(1000.0)


# --- conservation ---


def test_taint_conservation():
    """Total tainted at endpoints ≤ seed. Taint never increases."""
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
        ("t2", T0 + _m(minutes=20), "A", "C", 400.0, "USD"),
        ("t3", T0 + _m(minutes=30), "B", "D", 300.0, "USD"),
    ])
    result = trace(txns, "A", T0, 1000.0)
    total_tainted = sum(result.tainted_accounts.values())
    assert total_tainted <= 1000.0 + 1e-6


# --- edge cases ---


def test_missing_required_columns_raises():
    txns = pd.DataFrame({"txn_id": ["t1"]})
    with pytest.raises(ValueError, match="missing required columns"):
        trace(txns, "A", T0, 1000.0)


def test_empty_transactions_returns_valid_result():
    txns = _txns([])
    result = trace(txns, "A", T0, 1000.0)
    assert isinstance(result, TraceResult)
    assert result.seed_account == "A"
    assert result.tainted_edges == {}
    assert result.tainted_accounts.get("A", 0) == pytest.approx(1000.0)


def test_determinism():
    txns = _txns([
        ("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD"),
        ("t2", T0 + _m(minutes=20), "A", "C", 400.0, "USD"),
    ])
    r1 = trace(txns, "A", T0, 1000.0)
    r2 = trace(txns, "A", T0, 1000.0)
    assert r1.to_json() == r2.to_json()


def test_input_immutability():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    snapshot = txns.copy(deep=True)
    trace(txns, "A", T0, 1000.0)
    pd.testing.assert_frame_equal(txns, snapshot)


# --- SEE alert adapter ---


def test_trace_from_alert():
    txns = _txns([("t1", T0 + _m(minutes=10), "A", "B", 600.0, "USD")])
    alert = _alert("A")
    result = trace_from_alert(txns, alert, T0, 1000.0)
    assert result.alert_id == "see-test"
    assert result.seed_account == "A"
    assert result.tainted_accounts.get("B", 0) == pytest.approx(600.0)
 

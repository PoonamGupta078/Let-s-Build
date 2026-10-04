"""CUT tests: intervention recommendation engine."""
import math
import json
import pandas as pd
import pytest

from cut.config import CutConfig
from cut.models import CutRecommendation, CutResult
from cut.run import recommend, recommend_from_trace
from trace.models import TraceResult
from core.taint import run_taint, exit_taint
from core.freeze import plan, block_all, replay_curve

T0 = pd.Timestamp("2026-01-01 10:00")
m = lambda x: T0 + pd.Timedelta(minutes=x)


def df(rows):
    return pd.DataFrame(rows, columns=["txn_id", "ts", "src", "dst", "amount"])


RING = df([
    ("s1", m(10), "S", "M1", 500_000), ("s2", m(10), "S", "M2", 500_000),
    ("e1", m(40), "M1", "CASH", 500_000), ("e2", m(40), "M2", "CASH", 500_000),
])
SEEDS = {"S": (T0, 1_000_000)}
EXITS = {"CASH"}


# --- greedy strategy ---

def test_greedy_selects_top_accounts():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    assert r.strategy == "greedy"
    assert len(r.recommendations) == 2
    accounts = {rec.account for rec in r.recommendations}
    assert accounts == {"M1", "M2"}


def test_greedy_respects_max_recommendations():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=1))
    assert len(r.recommendations) == 1


def test_recommendation_ranking():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    ranks = [rec.rank for rec in r.recommendations]
    assert ranks == [1, 2]


def test_ties_ranked_deterministically():
    r1 = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    r2 = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    assert [rec.account for rec in r1.recommendations] == [rec.account for rec in r2.recommendations]


def test_evidence_txn_ids_populated():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    for rec in r.recommendations:
        assert len(rec.evidence_txn_ids) > 0


def test_estimated_tainted_blocked():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    for rec in r.recommendations:
        assert rec.estimated_tainted_blocked is not None
        assert rec.estimated_tainted_blocked > 0


def test_estimated_clean_disrupted():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    for rec in r.recommendations:
        assert rec.estimated_clean_disrupted is not None
        assert rec.estimated_clean_disrupted >= 0


def test_minutes_until_exit():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    for rec in r.recommendations:
        # eta should be a number (minutes to exit after t_alert)
        assert rec.minutes_until_exit is not None
        assert rec.minutes_until_exit > 0


def test_rationale_non_empty():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    for rec in r.recommendations:
        assert len(rec.rationale) > 10


def test_pct_blocked_is_percentage():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), config=CutConfig(max_recommendations=2))
    assert r.pct_blocked is not None
    assert 0 <= r.pct_blocked <= 100


def test_disclaimer_present():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20))
    assert "advisory" in r.disclaimer.lower()
    assert "no holds" in r.disclaimer.lower()


def test_late_alert_no_recommendations():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(50))
    assert len(r.recommendations) == 0
    assert r.pct_blocked == 0.0


def test_empty_transactions():
    """Valid empty input returns empty result, not an error."""
    empty = df([])
    r = recommend(empty, SEEDS, EXITS, t_alert=m(20))
    assert isinstance(r, CutResult)
    assert len(r.recommendations) == 0


def test_no_tainted_path_returns_empty():
    """Seed with no path to exits."""
    txns = df([("t1", m(10), "X", "Y", 100)])
    r = recommend(txns, {"X": (T0, 100)}, {"Z"}, t_alert=m(20))
    assert len(r.recommendations) == 0


# --- block_all strategy ---

def test_block_all_finds_chokepoints():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(0),
                  config=CutConfig(strategy="block_all"))
    assert r.strategy == "block_all"
    accounts = {rec.account for rec in r.recommendations}
    assert "S" in accounts  # source is chokepoint at t_alert=0


def test_block_all_rank_is_none():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(0),
                  config=CutConfig(strategy="block_all"))
    for rec in r.recommendations:
        assert rec.rank is None


def test_block_all_no_per_account_metrics():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(0),
                  config=CutConfig(strategy="block_all"))
    for rec in r.recommendations:
        assert rec.estimated_tainted_blocked is None
        assert rec.estimated_clean_disrupted is None
        assert rec.minutes_until_exit is None
        assert rec.evidence_txn_ids == ()


def test_block_all_aggregate_clean_held():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(0),
                  config=CutConfig(strategy="block_all"))
    assert r.aggregate_clean_held is not None
    assert r.aggregate_clean_held >= 0


def test_block_all_pct_blocked_none():
    """block_all doesn't compute per-account blocked, so pct_blocked is None."""
    r = recommend(RING, SEEDS, EXITS, t_alert=m(0),
                  config=CutConfig(strategy="block_all"))
    assert r.pct_blocked is None


# --- config validation ---

def test_invalid_strategy_raises():
    with pytest.raises(ValueError, match="strategy"):
        CutConfig(strategy="invalid")


def test_negative_hold_cost_raises():
    with pytest.raises(ValueError, match="hold_cost"):
        CutConfig(hold_cost=-1.0)


def test_zero_max_recommendations_raises():
    with pytest.raises(ValueError, match="max_recommendations"):
        CutConfig(max_recommendations=0)


# --- input validation ---

def test_missing_columns_raises():
    txns = pd.DataFrame({"txn_id": ["t1"]})
    with pytest.raises(ValueError, match="missing required columns"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20))


def test_naT_timestamp_raises():
    txns = df([("t1", pd.NaT, "S", "M1", 100)])
    with pytest.raises(ValueError, match="unparseable timestamps"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20))


def test_duplicate_txn_ids_raises():
    txns = df([("dup", m(10), "S", "M1", 100), ("dup", m(20), "S", "M2", 100)])
    with pytest.raises(ValueError, match="duplicate"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20))


def test_negative_amount_raises():
    txns = df([("t1", m(10), "S", "M1", -100)])
    with pytest.raises(ValueError, match="negative"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20))


# --- determinism and serialization ---

def test_deterministic_output():
    r1 = recommend(RING, SEEDS, EXITS, t_alert=m(20))
    r2 = recommend(RING, SEEDS, EXITS, t_alert=m(20))
    assert r1.to_json() == r2.to_json()


def test_json_serialization():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20))
    d = r.to_dict()
    s = r.to_json()
    assert isinstance(d, dict)
    assert isinstance(s, str)
    parsed = json.loads(s)
    assert parsed["strategy"] == "greedy"
    # Ensure no NaN/Inf in JSON
    assert "NaN" not in s
    assert "Infinity" not in s


def test_json_none_fields_for_block_all():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(0),
                  config=CutConfig(strategy="block_all"))
    d = r.to_dict()
    assert d["pct_blocked"] is None
    assert d["aggregate_clean_held"] is not None  # actually has a value
    for rec in d["recommendations"]:
        assert rec["rank"] is None
        assert rec["estimated_tainted_blocked"] is None


# --- trace integration ---

def test_recommend_from_trace_adapter():
    """recommend_from_trace extracts seeds from TraceResult correctly."""
    trace_result = TraceResult(
        alert_id="see-test", seed_account="S", seed_amount=1_000_000.0,
        seed_currency="USD", seed_ts=str(T0), config={},
        tainted_accounts={}, tainted_edges={},
        exit_taint_by_currency={}, paths=(),
    )
    r = recommend_from_trace(RING, trace_result, EXITS, t_alert=m(20))
    assert len(r.recommendations) > 0
    assert r.config["seed_currency"] == "USD"


def test_seed_not_inferred_from_alert_score():
    """Alert score is never used as seed amount."""
    trace_result = TraceResult(
        alert_id="see-test", seed_account="S", seed_amount=1_000_000.0,
        seed_currency="USD", seed_ts=str(T0), config={},
        tainted_accounts={}, tainted_edges={},
        exit_taint_by_currency={}, paths=(),
    )
    r = recommend_from_trace(RING, trace_result, EXITS, t_alert=m(20))
    # The seed amount is 1_000_000 (from TraceResult), not 100 (hypothetical alert score)
    assert r.baseline_exit_taint > 0


# --- zero baseline ---

def test_zero_baseline_pct_blocked():
    """When no taint reaches exits, pct_blocked is 0.0 not NaN."""
    txns = df([("t1", m(10), "S", "M1", 100)])
    r = recommend(txns, {"S": (T0, 50)}, {"CASH"}, t_alert=m(20))
    assert r.pct_blocked == 0.0


# --- currency ---

def test_seed_currency_recorded():
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20), seed_currency="USD")
    for rec in r.recommendations:
        assert rec.currency == "USD"
    assert r.config["seed_currency"] == "USD"


def test_unknown_currency_default():
    """No currency column + no seed_currency → records UNKNOWN."""
    r = recommend(RING, SEEDS, EXITS, t_alert=m(20))
    for rec in r.recommendations:
        assert rec.currency == "UNKNOWN"


def test_mixed_currencies_rejected():
    """Transaction data with multiple currencies must raise ValueError."""
    txns = pd.DataFrame([
        ("t1", m(10), "S", "M1", 500_000, "USD"),
        ("t2", m(10), "S", "M2", 500_000, "EUR"),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    with pytest.raises(ValueError, match="mixed currencies"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20))


def test_null_currency_values_rejected_without_seed_currency():
    """All-null currency column without seed_currency must raise ValueError."""
    txns = pd.DataFrame([
        ("t1", m(10), "S", "M1", 500_000, None),
        ("t2", m(10), "S", "M2", 500_000, None),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    with pytest.raises(ValueError, match="all values are missing"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20))


def test_null_currency_with_seed_currency_allowed():
    """All-null currency + explicit seed_currency → uses seed_currency."""
    txns = pd.DataFrame([
        ("s1", m(10), "S", "M1", 500_000, None),
        ("s2", m(10), "S", "M2", 500_000, None),
        ("e1", m(40), "M1", "CASH", 500_000, None),
        ("e2", m(40), "M2", "CASH", 500_000, None),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    r = recommend(txns, SEEDS, EXITS, t_alert=m(20), seed_currency="USD")
    assert r.config["seed_currency"] == "USD"
    assert len(r.recommendations) > 0


def test_seed_currency_conflicts_with_data():
    """seed_currency="EUR" but data has only USD → must raise ValueError."""
    txns = pd.DataFrame([
        ("s1", m(10), "S", "M1", 500_000, "USD"),
        ("s2", m(10), "S", "M2", 500_000, "USD"),
        ("e1", m(40), "M1", "CASH", 500_000, "USD"),
        ("e2", m(40), "M2", "CASH", 500_000, "USD"),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    with pytest.raises(ValueError, match="does not match"):
        recommend(txns, SEEDS, EXITS, t_alert=m(20), seed_currency="EUR")


def test_trace_seed_currency_conflicts_with_data():
    """recommend_from_trace must raise when trace seed currency mismatches txn data."""
    txns = pd.DataFrame([
        ("s1", m(10), "S", "M1", 500_000, "USD"),
        ("s2", m(10), "S", "M2", 500_000, "USD"),
        ("e1", m(40), "M1", "CASH", 500_000, "USD"),
        ("e2", m(40), "M2", "CASH", 500_000, "USD"),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    trace_result = TraceResult(
        alert_id="see-test", seed_account="S", seed_amount=1_000_000.0,
        seed_currency="EUR", seed_ts=str(T0), config={},
        tainted_accounts={}, tainted_edges={},
        exit_taint_by_currency={}, paths=(),
    )
    with pytest.raises(ValueError, match="does not match"):
        recommend_from_trace(txns, trace_result, EXITS, t_alert=m(20))


def test_valid_single_currency_with_column():
    """Single-currency data with matching seed_currency works correctly."""
    txns = pd.DataFrame([
        ("s1", m(10), "S", "M1", 500_000, "USD"),
        ("s2", m(10), "S", "M2", 500_000, "USD"),
        ("e1", m(40), "M1", "CASH", 500_000, "USD"),
        ("e2", m(40), "M2", "CASH", 500_000, "USD"),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    r = recommend(txns, SEEDS, EXITS, t_alert=m(20), seed_currency="USD")
    assert len(r.recommendations) > 0
    for rec in r.recommendations:
        assert rec.currency == "USD"


def test_single_currency_without_seed_currency_infers():
    """Single currency in data, no seed_currency → infers from data."""
    txns = pd.DataFrame([
        ("s1", m(10), "S", "M1", 500_000, "GBP"),
        ("s2", m(10), "S", "M2", 500_000, "GBP"),
        ("e1", m(40), "M1", "CASH", 500_000, "GBP"),
        ("e2", m(40), "M2", "CASH", 500_000, "GBP"),
    ], columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    r = recommend(txns, SEEDS, EXITS, t_alert=m(20))
    assert r.config["seed_currency"] == "GBP"


# --- core regression ---

def test_core_plan_regression():
    """Verify core.freeze.plan still works identically on RING fixture."""
    p = plan(RING, SEEDS, EXITS, t_alert=m(20), k=2)
    assert p["pct_blocked"] > 99 and len(p["holds"]) == 2
    assert plan(RING, SEEDS, EXITS, m(20), k=1)["pct_blocked"] == 50.0


def test_core_block_all_regression():
    assert set(block_all(RING, SEEDS, EXITS, m(20))["holds"]) == {"M1", "M2"}
    assert block_all(RING, SEEDS, EXITS, m(0))["holds"] == ["S"]


def test_core_replay_curve_regression():
    c = [p for _, p in replay_curve(RING, SEEDS, EXITS, m(0), [0, 20, 60], k=2)]
    assert c[0] >= c[1] >= c[2]


def test_core_taint_regression():
    """Verify core.taint.run_taint still works identically."""
    tx = df([("x", m(0), "X", "C", 3_000_000), ("ab", m(10), "A", "B", 1_000_000),
             ("bc", m(20), "B", "C", 1_000_000), ("cd", m(30), "C", "D", 2_000_000)])
    r = run_taint(tx, {"A": (m(0), 1_000_000)})
    assert abs(r["edge"]["cd"] - 500_000) < 1e-6

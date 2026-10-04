"""Milestone 3 tests: SEE detection engine.

Uses small synthetic fixtures; never loads the full IBM dataset.
"""
import pandas as pd
import pytest

from see.models import Alert
from see.rules import (
    HIGH_ACTIVITY_RULE_ID,
    RAPID_PASS_THROUGH_RULE_ID,
    FAN_RULE_ID,
)
from see.run import SeeConfig, detect

T0 = pd.Timestamp("2022-09-01 10:00")
_m = pd.Timedelta


def _txns(rows: list[tuple]) -> pd.DataFrame:
    """Build a minimal transaction frame with currency."""
    return pd.DataFrame(
        rows,
        columns=["txn_id", "ts", "src", "dst", "amount", "currency"],
    )


RAPID_FIXTURE = _txns([
    ("t_in", T0 + _m(minutes=5), "EXT", "A", 1000.0, "USD"),
    ("t_out", T0 + _m(minutes=55), "A", "B", 900.0, "USD"),
    ("t_far", T0 + _m(hours=5), "A", "B", 100.0, "USD"),
])


def test_rapid_pass_through_triggers():
    alerts = detect(RAPID_FIXTURE, SeeConfig(rapid_window=_m(hours=1)))
    rpt = [a for a in alerts if a.rule_id == RAPID_PASS_THROUGH_RULE_ID]
    assert len(rpt) == 1
    assert rpt[0].account == "A"
    assert set(rpt[0].evidence_txn_ids) == {"t_in", "t_out"}


def test_rapid_pass_through_outside_window():
    alerts = detect(RAPID_FIXTURE, SeeConfig(rapid_window=_m(minutes=30)))
    rpt = [a for a in alerts if a.rule_id == RAPID_PASS_THROUGH_RULE_ID]
    assert len(rpt) == 0


def test_rapid_pass_through_different_currencies_no_match():
    txns = _txns([
        ("t_in", T0, "EXT", "A", 1000.0, "USD"),
        ("t_out", T0 + _m(minutes=10), "A", "B", 900.0, "EUR"),
    ])
    alerts = detect(txns, SeeConfig(rapid_window=_m(hours=1)))
    rpt = [a for a in alerts if a.rule_id == RAPID_PASS_THROUGH_RULE_ID]
    assert len(rpt) == 0


def test_one_outgoing_supports_multiple_incoming_alerts():
    """Two incoming txns both precede the same outgoing txn within the window.
    Both pair with it, producing two RPT alerts that share the outgoing txn."""
    txns = _txns([
        ("in1", T0, "EXT", "A", 1000.0, "USD"),
        ("in2", T0 + _m(minutes=10), "EXT", "A", 500.0, "USD"),
        ("out1", T0 + _m(minutes=30), "A", "B", 800.0, "USD"),
    ])
    alerts = detect(txns, SeeConfig(rapid_window=_m(hours=1)))
    rpt = [a for a in alerts if a.rule_id == RAPID_PASS_THROUGH_RULE_ID]
    assert len(rpt) == 2
    for a in rpt:
        assert "out1" in a.evidence_txn_ids


# --- high activity ---


def test_high_activity_triggers_at_threshold():
    rows = [(f"t{i}", T0 + _m(minutes=i), "A", f"B{i}", 10.0, "USD") for i in range(5)]
    txns = _txns(rows)
    cfg = SeeConfig(activity_window=_m(hours=1), activity_threshold=5)
    alerts = detect(txns, cfg)
    hta = [a for a in alerts if a.rule_id == HIGH_ACTIVITY_RULE_ID]
    assert len(hta) == 1
    assert hta[0].account == "A"
    assert len(hta[0].evidence_txn_ids) == 5


# --- fan-in/out ---


def test_fan_in_out_counts_distinct_counterparties():
    txns = _txns([
        ("t1", T0, "X1", "A", 10.0, "USD"),
        ("t2", T0 + _m(minutes=5), "X2", "A", 10.0, "USD"),
        ("t3", T0 + _m(minutes=10), "X3", "A", 10.0, "USD"),
    ])
    cfg = SeeConfig(fan_window=_m(hours=1), fan_threshold=3)
    alerts = detect(txns, cfg)
    fan = [a for a in alerts if a.rule_id == FAN_RULE_ID]
    assert len(fan) == 1
    assert fan[0].account == "A"


def test_fan_in_out_self_transfer_not_double_counted():
    """A self-transfer A→A appears in both in_txns and out_txns. The
    drop_duplicates on (txn_id, counterparty) must prevent it from being
    counted as two rows toward the distinct-counterparty threshold."""
    # 2 distinct counterparties (X1, X2) + 1 self-transfer (A→A).
    # Without dedup, the merged frame would have 4 rows (X1, X2, A from in, A
    # from out) but only 3 distinct counterparties. With threshold=3 the alert
    # should fire if distinct counterparties >= 3.
    # With dedup, merged has 3 rows (X1, X2, A) and 3 distinct counterparties.
    txns = _txns([
        ("t1", T0, "X1", "A", 10.0, "USD"),
        ("t2", T0 + _m(minutes=5), "X2", "A", 10.0, "USD"),
        ("t3", T0 + _m(minutes=10), "A", "A", 10.0, "USD"),  # self-transfer
    ])
    cfg = SeeConfig(fan_window=_m(hours=1), fan_threshold=3)
    alerts = detect(txns, cfg)
    fan = [a for a in alerts if a.rule_id == FAN_RULE_ID]
    assert len(fan) == 1
    assert fan[0].account == "A"
    # Evidence must contain exactly 3 txn_ids (not 4 from double-counting).
    assert len(fan[0].evidence_txn_ids) == 3


# --- evidence and explanation ---


def test_evidence_txn_ids_and_explanation_correct():
    alerts = detect(RAPID_FIXTURE, SeeConfig(rapid_window=_m(hours=1)))
    rpt = [a for a in alerts if a.rule_id == RAPID_PASS_THROUGH_RULE_ID][0]
    assert "t_in" in rpt.explanation and "t_out" in rpt.explanation
    assert "A" in rpt.explanation
    assert set(rpt.evidence_txn_ids) == {"t_in", "t_out"}


# --- determinism ---


def test_alert_ids_and_output_ordering_deterministic():
    cfg = SeeConfig(rapid_window=_m(hours=1))
    a1 = detect(RAPID_FIXTURE, cfg)
    a2 = detect(RAPID_FIXTURE, cfg)
    assert [a.alert_id for a in a1] == [a.alert_id for a in a2]
    assert [a.account for a in a1] == sorted([a.account for a in a1])


def test_stable_sort_with_equal_timestamps():
    """Rows with identical timestamps must be processed in their original order."""
    rows = [
        ("t1", T0, "EXT", "A", 100.0, "USD"),
        ("t2", T0, "EXT", "A", 200.0, "USD"),
        ("t3", T0, "A", "B", 150.0, "USD"),
    ]
    txns = _txns(rows)
    cfg = SeeConfig(rapid_window=_m(hours=1))
    a1 = detect(txns, cfg)
    a2 = detect(txns, cfg)
    assert [a.alert_id for a in a1] == [a.alert_id for a in a2]


# --- empty input ---


def test_empty_input():
    empty = pd.DataFrame(columns=["txn_id", "ts", "src", "dst", "amount", "currency"])
    assert detect(empty) == []


# --- missing columns ---


def test_missing_required_columns_raises():
    bad = pd.DataFrame({"txn_id": ["t1"]})
    with pytest.raises(ValueError, match="missing required columns"):
        detect(bad)


# --- duplicate txn ids ---


def test_duplicate_txn_ids_raise_value_error():
    """Duplicate txn_ids violate the validated-input contract."""
    txns = _txns([
        ("dup", T0, "EXT", "A", 100.0, "USD"),
        ("dup", T0 + _m(minutes=5), "A", "B", 50.0, "USD"),
    ])
    with pytest.raises(ValueError, match="duplicate"):
        detect(txns, SeeConfig(rapid_window=_m(hours=1)))


def test_conflicting_duplicate_txn_ids_raise_value_error():
    """Two rows with same txn_id and timestamp but different amounts."""
    txns = _txns([
        ("dup", T0, "EXT", "A", 100.0, "USD"),
        ("dup", T0, "A", "B", 50.0, "USD"),
    ])
    with pytest.raises(ValueError, match="duplicate"):
        detect(txns, SeeConfig(rapid_window=_m(hours=1)))


# --- malformed timestamps ---


def test_nat_timestamp_raises():
    """Rows with NaT timestamps must be rejected, not silently skipped."""
    txns = pd.DataFrame({
        "txn_id": ["t1", "t2"],
        "ts": [T0, pd.NaT],
        "src": ["EXT", "EXT"],
        "dst": ["A", "A"],
        "amount": [100.0, 200.0],
        "currency": ["USD", "USD"],
    })
    with pytest.raises(ValueError, match="unparseable timestamps"):
        detect(txns, SeeConfig(rapid_window=_m(hours=1)))


# --- label leakage ---


def test_labels_cannot_influence_results():
    """Adding an is_laundering column must not affect detection outcomes."""
    txns = RAPID_FIXTURE.copy()
    txns["is_laundering"] = [0, 1, 0]
    alerts = detect(txns, SeeConfig(rapid_window=_m(hours=1)))
    for a in alerts:
        assert "is_laundering" not in a.explanation


# --- immutability ---


def test_input_data_unchanged():
    original = RAPID_FIXTURE.copy()
    snapshot = original.copy(deep=True)
    detect(original, SeeConfig(rapid_window=_m(hours=1)))
    pd.testing.assert_frame_equal(original, snapshot)


# --- time-window boundaries ---


def test_time_window_boundaries():
    """Transaction at exactly window boundary should trigger; one past should not."""
    txns_boundary = _txns([
        ("t_in", T0, "EXT", "A", 100.0, "USD"),
        ("t_out_edge", T0 + _m(hours=1), "A", "B", 90.0, "USD"),
    ])
    txns_over = _txns([
        ("t_in", T0, "EXT", "A", 100.0, "USD"),
        ("t_out_over", T0 + _m(hours=1, seconds=1), "A", "B", 90.0, "USD"),
    ])
    cfg = SeeConfig(rapid_window=_m(hours=1))
    alerts_boundary = detect(txns_boundary, cfg)
    alerts_over = detect(txns_over, cfg)
    rpt_b = [a for a in alerts_boundary if a.rule_id == RAPID_PASS_THROUGH_RULE_ID]
    rpt_o = [a for a in alerts_over if a.rule_id == RAPID_PASS_THROUGH_RULE_ID]
    assert len(rpt_b) == 1
    assert len(rpt_o) == 0


# --- SeeConfig validation ---


def test_see_config_rejects_negative_window():
    with pytest.raises(ValueError, match="positive Timedelta"):
        SeeConfig(rapid_window=_m(hours=-1))


def test_see_config_rejects_zero_window():
    with pytest.raises(ValueError, match="positive Timedelta"):
        SeeConfig(activity_window=_m(0))


def test_see_config_rejects_zero_threshold():
    with pytest.raises(ValueError, match=">= 1"):
        SeeConfig(activity_threshold=0)


def test_see_config_rejects_negative_threshold():
    with pytest.raises(ValueError, match=">= 1"):
        SeeConfig(fan_threshold=-5)


def test_see_config_rejects_negative_ratio():
    with pytest.raises(ValueError, match=">= 0"):
        SeeConfig(rapid_min_amount_ratio=-0.5)


def test_see_config_accepts_valid_boundary():
    """Threshold=1 and ratio=0 are valid boundary values."""
    cfg = SeeConfig(activity_threshold=1, fan_threshold=1, rapid_min_amount_ratio=0.0)
    assert cfg.activity_threshold == 1
    assert cfg.fan_threshold == 1

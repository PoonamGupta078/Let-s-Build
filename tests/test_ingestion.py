"""Milestone 1 tests: IBM AML ingestion, normalization and validation (acceptance test #9).

Fixtures in tests/fixtures/ use the REAL column layout of HI-Small_Trans.csv /
HI-Small_accounts.csv (verified against the actual files), including rows that
deliberately violate validation rules.
"""
import json
from pathlib import Path

import pandas as pd

from ingestion.load import (
    load_ibm_accounts,
    load_ibm_raw,
    process_ibm_dataset,
    reproducible_sample,
)
from ingestion.schema import INTERNAL_TXN_COLUMNS, normalize_ibm_transactions
from ingestion.validate import ValidationPolicy, validate_transactions

FIXTURES = Path(__file__).parent / "fixtures"
TRANS_FIXTURE = FIXTURES / "hi_small_trans_sample.csv"
ACCOUNTS_FIXTURE = FIXTURES / "hi_small_accounts_sample.csv"
T0 = pd.Timestamp("2022-09-01 00:00")

# Fixture expectations: 12 raw rows, 5 invalid (2 self-transfers, 1 negative
# amount, 1 bad timestamp, 1 missing destination), 7 accepted, 3 labeled.
N_ACCEPTED = 7


def internal_frame(rows: list) -> pd.DataFrame:
    """Build an internal-schema frame from tuples of the 8 core values."""
    return pd.DataFrame(rows, columns=INTERNAL_TXN_COLUMNS)


def test_validator_rejects_negative_amount():
    txns = internal_frame([
        ("t1", T0, "A", "B", 100.0, "transfer", "NEFT", False),
        ("t2", T0, "A", "B", -5.0, "transfer", "NEFT", False),
    ])
    report = validate_transactions(txns)
    assert report.counts["total"] == 2
    assert report.counts["accepted"] == 1
    assert report.counts["negative_amount"] == 1
    assert list(report.accepted["txn_id"]) == ["t1"]
    assert report.rejected.iloc[0]["txn_id"] == "t2"
    assert report.rejected.iloc[0]["_rules"] == "negative_amount"


def test_validator_rejects_self_transfer():
    txns = internal_frame([("t1", T0, "A", "A", 10.0, "transfer", "NEFT", False)])
    report = validate_transactions(txns)
    assert report.counts["self_transfer"] == 1
    assert report.counts["accepted"] == 0


def test_self_transfer_policy_is_configurable():
    """IBM data contains legitimate 'Reinvestment' self-transfers; keep- or
    reject-policy is an explicit, documented choice."""
    txns = internal_frame([("t1", T0, "A", "A", 10.0, "transfer", "NEFT", False)])
    keep = validate_transactions(txns, ValidationPolicy(reject_self_transfers=False))
    assert keep.counts["accepted"] == 1
    assert keep.counts["rejected"] == 0


def test_validator_rejects_missing_ids_and_bad_timestamps_and_amounts():
    txns = internal_frame([
        ("t1", pd.NaT, "A", "B", 10.0, "transfer", "NEFT", False),
        ("", T0, "A", "B", 10.0, "transfer", "NEFT", False),
        ("t3", T0, "", "B", 10.0, "transfer", "NEFT", False),
        ("t4", T0, "A", None, 10.0, "transfer", "NEFT", False),
        ("t5", T0, "A", "B", float("nan"), "transfer", "NEFT", False),
        ("t6", T0, "A", "B", float("inf"), "transfer", "NEFT", False),
        ("t7", T0, "A", "B", 10.0, "transfer", "NEFT", False),
    ])
    report = validate_transactions(txns)
    assert report.counts["bad_timestamp"] == 1
    assert report.counts["missing_id"] == 3
    assert report.counts["bad_amount"] == 2
    assert report.counts["accepted"] == 1


def test_zero_amount_is_accepted_by_default():
    """Spec requires non-negative amounts: zero is valid, negative is not."""
    txns = internal_frame([("t1", T0, "A", "B", 0.0, "transfer", "NEFT", False)])
    assert validate_transactions(txns).counts["accepted"] == 1


def test_validation_counts_are_complete():
    """AC #9: every rule's rejection count is shown, and accepted+rejected=total."""
    txns = internal_frame([
        ("t1", T0, "A", "B", -1.0, "transfer", "NEFT", False),
        ("t2", T0, "C", "C", 5.0, "transfer", "NEFT", False),
        ("t2", T0, "A", "B", 5.0, "transfer", "NEFT", False),
        ("t3", T0, "A", "B", 5.0, "transfer", "NEFT", False),
    ])
    report = validate_transactions(txns)
    assert report.counts["total"] == 4
    assert report.counts["accepted"] + report.counts["rejected"] == 4
    for rule in ("negative_amount", "self_transfer", "duplicate_txn_id"):
        assert report.counts[rule] == 1


def test_ibm_normalization_maps_real_schema():
    raw = load_ibm_raw(TRANS_FIXTURE)
    txns, labels = normalize_ibm_transactions(raw)

    assert list(txns.columns) == INTERNAL_TXN_COLUMNS + ["currency"]
    assert "Is Laundering" not in txns.columns
    assert "is_laundering" not in txns.columns
    assert txns["txn_id"].tolist() == [f"hi-{i:08d}" for i in range(1, 13)]

    row = txns.set_index("txn_id").loc["hi-00000002"]
    assert row["src"] == "8000F4580"
    assert row["dst"] == "8000F5340"
    assert bool(row["ext_bank"]) is True          # banks 03208 -> 001 differ
    assert row["channel"] == "Cheque"
    assert row["amount"] == 0.01
    assert row["currency"] == "US Dollar"

    same_bank = txns.set_index("txn_id").loc["hi-00000008"]
    assert bool(same_bank["ext_bank"]) is False   # 030 -> 030

    assert labels.name == "is_laundering"
    assert int(labels.sum()) == 3                 # rows 4, 10, 11 are labeled
    assert int(labels.loc["hi-00000004"]) == 1

    # 12 rows parsed; one deliberately bad timestamp becomes NaT, not dropped.
    assert len(txns) == 12
    assert int(txns["ts"].isna().sum()) == 1


def test_process_ibm_dataset_writes_outputs_and_preserves_raw(tmp_path):
    original_bytes = TRANS_FIXTURE.read_bytes()
    out_dir = tmp_path / "processed"
    sample_dir = tmp_path / "samples"

    summary = process_ibm_dataset(
        TRANS_FIXTURE,
        ACCOUNTS_FIXTURE,
        out_dir,
        sample_size=3,
        sample_dir=sample_dir,
    )

    for name in ("transactions.csv", "labels.csv", "accounts.csv", "data_quality.json"):
        assert (out_dir / name).exists(), f"missing output {name}"

    txns = pd.read_csv(out_dir / "transactions.csv")
    assert len(txns) == N_ACCEPTED == summary["counts"]["accepted"]
    assert "is_laundering" not in txns.columns
    assert txns["ts"].is_monotonic_increasing  # time-sorted for downstream use

    labels = pd.read_csv(out_dir / "labels.csv")
    assert len(labels) == N_ACCEPTED
    assert int(labels["is_laundering"].sum()) == 3

    accounts = pd.read_csv(out_dir / "accounts.csv", dtype=str)
    assert list(accounts.columns) == [
        "account_id", "bank_id", "bank_name", "entity_id", "entity_name",
    ]
    assert accounts["account_id"].tolist()[1] == "809D86900"
    assert accounts["bank_id"].tolist()[1] == "210"  # leading zero preserved

    quality = json.loads((out_dir / "data_quality.json").read_text())
    assert quality["counts"] == summary["counts"]
    assert quality["counts"]["self_transfer"] == 2
    assert quality["counts"]["negative_amount"] == 1
    assert quality["counts"]["bad_timestamp"] == 1
    assert quality["counts"]["missing_id"] == 1

    sample = pd.read_csv(sample_dir / "sample_transactions.csv")
    assert len(sample) == 3
    assert sample["ts"].is_monotonic_increasing

    assert TRANS_FIXTURE.read_bytes() == original_bytes  # raw untouched


def test_reproducible_sample_is_deterministic():
    txns = internal_frame([
        (f"t{i:02d}", T0 + pd.Timedelta(minutes=i), "A", "B", float(i),
         "transfer", "NEFT", False) for i in range(10)
    ])
    first = reproducible_sample(txns, 4)
    second = reproducible_sample(txns, 4)
    assert first.equals(second)
    assert len(first) == 4
    assert first["ts"].is_monotonic_increasing
    assert len(reproducible_sample(txns, 100)) == 10  # cap at frame size
def test_validator_rejects_duplicate_txn_id_keeping_first():
    txns = internal_frame([
        ("t1", T0, "A", "B", 10.0, "transfer", "NEFT", False),
        ("t1", T0, "B", "C", 20.0, "transfer", "NEFT", False),
        ("t2", T0, "B", "C", 20.0, "transfer", "NEFT", False),
    ])
    report = validate_transactions(txns)
    assert report.counts["duplicate_txn_id"] == 1
    assert list(report.accepted["txn_id"]) == ["t1", "t2"]
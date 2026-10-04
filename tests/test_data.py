import pandas as pd
from pandas.testing import assert_frame_equal

from data.make_case import make_case


def test_case_dataset_has_core_schema_and_explicit_metadata():
    case = make_case(background_rows=0)

    assert list(case.transactions.columns) == [
        "txn_id", "ts", "src", "dst", "amount", "type", "channel", "ext_bank"
    ]
    assert case.seeds == {"S": (pd.Timestamp("2026-01-01 10:00"), 1_000_000.0)}
    assert case.exits == {"CASH"}
    assert case.accounts.set_index("account_id").loc["CASH", "role"] == "EXIT"
    assert "is_laundering" not in case.transactions.columns


def test_case_dataset_is_deterministic_and_traceable():
    first = make_case(seed=42, background_rows=12)
    second = make_case(seed=42, background_rows=12)

    assert_frame_equal(first.transactions, second.transactions)
    assert_frame_equal(first.accounts, second.accounts)
    assert first.transactions["ts"].is_monotonic_increasing

    trail = first.transactions.set_index("txn_id")
    assert trail.loc["case-001", ["src", "dst", "amount"]].to_dict() == {
        "src": "S", "dst": "M1", "amount": 500_000.0
    }
    assert trail.loc["case-004", ["src", "dst", "amount"]].to_dict() == {
        "src": "M2", "dst": "CASH", "amount": 500_000.0
    }
    assert len(first.transactions) == 4 + 12


def test_background_rows_do_not_touch_the_controlled_case():
    case = make_case(background_rows=25)
    background = case.transactions[case.transactions["txn_id"].str.startswith("bg-")]

    assert len(background) == 25
    assert not background["src"].isin({"S", "M1", "M2", "CASH"}).any()
    assert not background["dst"].isin({"S", "M1", "M2", "CASH"}).any()
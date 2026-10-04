"""Build a deterministic AML investigation case and isolated background traffic."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


TRANSACTION_COLUMNS = [
    "txn_id", "ts", "src", "dst", "amount", "type", "channel", "ext_bank"
]
ACCOUNT_COLUMNS = ["account_id", "role", "is_exit"]


@dataclass
class CaseDataset:
    """Transactions and investigation metadata for a generated demo case."""

    transactions: pd.DataFrame
    accounts: pd.DataFrame
    seeds: dict[str, tuple[pd.Timestamp, float]]
    exits: set[str]
    suspicious_accounts: set[str]


def make_case(seed: int = 42, background_rows: int = 100) -> CaseDataset:
    """Create a two-mule cash-out trail with reproducible unrelated transfers."""
    if isinstance(background_rows, bool) or not isinstance(background_rows, int):
        raise TypeError("background_rows must be an integer")
    if background_rows < 0:
        raise ValueError("background_rows cannot be negative")

    start = pd.Timestamp("2026-01-01 10:00:00")
    case_transactions = pd.DataFrame(
        [
            ("case-001", start + pd.Timedelta(minutes=10), "S", "M1", 500_000.0,
             "transfer", "NEFT", False),
            ("case-002", start + pd.Timedelta(minutes=10), "S", "M2", 500_000.0,
             "transfer", "NEFT", False),
            ("case-003", start + pd.Timedelta(minutes=40), "M1", "CASH", 500_000.0,
             "cash_out", "ATM", False),
            ("case-004", start + pd.Timedelta(minutes=40), "M2", "CASH", 500_000.0,
             "cash_out", "ATM", False),
        ],
        columns=TRANSACTION_COLUMNS,
    )

    background = _make_background(start, seed, background_rows)
    transactions = pd.concat([case_transactions, background], ignore_index=True)
    transactions = transactions.sort_values(
        ["ts", "txn_id"], kind="mergesort"
    ).reset_index(drop=True)

    background_accounts = sorted(
        set(background["src"]) | set(background["dst"])
    ) if not background.empty else []
    accounts = pd.DataFrame(
        [
            ("S", "SOURCE", False),
            ("M1", "MULE", False),
            ("M2", "MULE", False),
            ("CASH", "EXIT", True),
            *((account_id, "NORMAL", False) for account_id in background_accounts),
        ],
        columns=ACCOUNT_COLUMNS,
    )

    return CaseDataset(
        transactions=transactions,
        accounts=accounts,
        seeds={"S": (start, 1_000_000.0)},
        exits={"CASH"},
        suspicious_accounts={"S"},
    )


def _make_background(start: pd.Timestamp, seed: int, row_count: int) -> pd.DataFrame:
    if row_count == 0:
        return pd.DataFrame(columns=TRANSACTION_COLUMNS)

    rng = np.random.default_rng(seed)
    account_count = max(2, min(row_count, 20))
    account_ids = [f"BG{index:03d}" for index in range(account_count)]
    source_indices = rng.integers(0, account_count, size=row_count)
    destination_indices = rng.integers(0, account_count, size=row_count)
    same_account = source_indices == destination_indices
    destination_indices[same_account] = (
        destination_indices[same_account] + 1
    ) % account_count

    offsets = rng.integers(1, 1_441, size=row_count)
    amounts = rng.integers(5_000, 250_001, size=row_count)
    channels = rng.choice(["UPI", "NEFT", "IMPS", "net_banking"], size=row_count)

    return pd.DataFrame(
        {
            "txn_id": [f"bg-{index:06d}" for index in range(row_count)],
            "ts": start + pd.to_timedelta(offsets, unit="m"),
            "src": [account_ids[index] for index in source_indices],
            "dst": [account_ids[index] for index in destination_indices],
            "amount": amounts.astype(float),
            "type": "transfer",
            "channel": channels,
            "ext_bank": False,
        },
        columns=TRANSACTION_COLUMNS,
    )
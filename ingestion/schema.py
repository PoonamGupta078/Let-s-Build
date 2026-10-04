"""Internal transaction schema and normalization from the IBM AML CSV layout.

The IBM layout below was read from the actual data/HI-Small_Trans.csv header
(verified 2026-10-04, not taken from documentation):

    Timestamp, From Bank, Account, To Bank, Account, Amount Received,
    Receiving Currency, Amount Paid, Payment Currency, Payment Format, Is Laundering

pandas mangles the duplicate 'Account' header to 'Account.1' on read.

Mapping decisions (documented, deliberate):
  txn_id   generated deterministically from row order: hi-00000001, ...
  ts       Timestamp parsed with the fixed format '%Y/%m/%d %H:%M'
  src/dst  Account / Account.1 (kept as strings: ids are hex-like, banks have
           leading zeros such as '010')
  amount   Amount Paid — what left the source account, in Payment Currency
  type     'transfer' — IBM has no separate type field
  channel  Payment Format (Cheque, Wire, Reinvestment, ...)
  ext_bank True when From Bank != To Bank (funds leave the institution)
  currency Payment Currency, kept as an extra column: IBM amounts are in many
           currencies and raw amounts must never be compared across currencies

'Is Laundering' is a ground-truth LABEL: it is split into a separate Series
for evaluation ONLY and must never appear in the transaction frame, graph
edges or model features (project rule).
"""
from __future__ import annotations

import pandas as pd

# Core internal schema: identical columns to data/make_case.py.
INTERNAL_TXN_COLUMNS = [
    "txn_id", "ts", "src", "dst", "amount", "type", "channel", "ext_bank",
]
# Extra preserved column (see module docstring).
CURRENCY_COLUMN = "currency"

IBM_TIMESTAMP_FORMAT = "%Y/%m/%d %H:%M"
IBM_TXN_LABEL_COLUMN = "Is Laundering"


def ibm_string_dtypes() -> dict[str, str]:
    """Columns that must be read as strings to preserve leading zeros."""
    return {
        "From Bank": "string", "To Bank": "string",
        "Account": "string", "Account.1": "string",
        "Payment Format": "string", "Payment Currency": "string",
    }


def normalize_ibm_transactions(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Map a raw IBM transaction frame to the internal schema.

    Unparseable timestamps/amounts become NaT/NaN and are left for
    validate_transactions to reject explicitly — nothing is dropped here.
    Returns (txns, labels): labels is an Int64 Series named 'is_laundering'
    indexed by txn_id, intended for evaluation only.
    """
    df = raw.reset_index(drop=True)
    txn_ids = [f"hi-{i:08d}" for i in range(1, len(df) + 1)]
    txns = pd.DataFrame(
        {
            "txn_id": txn_ids,
            "ts": pd.to_datetime(
                df["Timestamp"], format=IBM_TIMESTAMP_FORMAT, errors="coerce"
            ),
            "src": df["Account"].astype("string"),
            "dst": df["Account.1"].astype("string"),
            "amount": pd.to_numeric(df["Amount Paid"], errors="coerce"),
            "type": "transfer",
            "channel": df["Payment Format"].astype("string"),
            "ext_bank": df["From Bank"].astype("string").ne(
                df["To Bank"].astype("string")
            ),
            CURRENCY_COLUMN: df["Payment Currency"].astype("string"),
        }
    )
    labels = pd.Series(
        pd.to_numeric(df[IBM_TXN_LABEL_COLUMN], errors="coerce").to_numpy(),
        index=txn_ids,
        name="is_laundering",
        dtype="Int64",
    )
    return txns, labels
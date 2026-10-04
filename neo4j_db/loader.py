"""Safe, limited Neo4j loader for accounts and transactions.

Writes in parameterized batches.  Idempotent: rerunning does not create
duplicates.  Does NOT write evaluation labels.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from ingestion.schema import INTERNAL_TXN_COLUMNS, CURRENCY_COLUMN


_REQUIRED_TXN_COLS = {"txn_id", "ts", "src", "dst", "amount"}

# Approved fields only — labels excluded.
_TXN_PROPS = [
    "txn_id", "ts", "amount", "type", "channel", "ext_bank", "currency",
]


@dataclass
class LoadReport:
    accounts_processed: int = 0
    accounts_created: int = 0
    transactions_processed: int = 0
    transactions_created: int = 0
    rejected: int = 0
    warnings: list[str] = None

    def __post_init__(self) -> None:
        if self.warnings is None:
            self.warnings = []


# -- validation helpers -----------------------------------------------------


def _validate_txns(txns: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return (clean_txns, rejected_count).  Rejects rows with missing IDs,
    NaT timestamps, or non-finite amounts."""
    missing = _REQUIRED_TXN_COLS - set(txns.columns)
    if missing:
        raise ValueError(f"input missing required columns: {sorted(missing)}")
    df = txns.copy()
    mask = (
        df["txn_id"].isna()
        | df["src"].isna()
        | df["dst"].isna()
        | df["ts"].isna()
        | df["amount"].isna()
    )
    rejected = int(mask.sum())
    return df.loc[~mask].reset_index(drop=True), rejected


# -- Cypher statements (parameterized) --------------------------------------

_MERGE_ACCOUNT = """
UNWIND $accounts AS a
MERGE (acct:Account {account_id: a.account_id})
"""

_MERGE_TRANSFER = """
UNWIND $txns AS t
MATCH (src:Account {account_id: t.src})
MATCH (dst:Account {account_id: t.dst})
MERGE (src)-[rel:TRANSFER {txn_id: t.txn_id}]->(dst)
SET rel.ts       = datetime(t.ts),
    rel.amount   = t.amount,
    rel.type     = t.type,
    rel.channel  = t.channel,
    rel.ext_bank = t.ext_bank,
    rel.currency = t.currency
"""


def _prepare_accounts(accounts: pd.DataFrame) -> list[dict[str, Any]]:
    if "account_id" not in accounts.columns:
        raise ValueError("accounts DataFrame must contain 'account_id'")
    records: list[dict[str, Any]] = []
    for _, row in accounts.iterrows():
        aid = row["account_id"]
        if pd.notna(aid):
            records.append({"account_id": str(aid)})
    return records


def _prepare_txns(txns: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert validated DataFrame rows to dicts for parameterized queries."""
    records: list[dict[str, Any]] = []
    for _, row in txns.iterrows():
        rec: dict[str, Any] = {
            "src": str(row["src"]),
            "dst": str(row["dst"]),
        }
        for col in _TXN_PROPS:
            val = row.get(col) if hasattr(row, "get") else getattr(row, col, None)
            if val is None:
                continue
            if isinstance(val, pd.Timestamp):
                rec[col] = val.isoformat()
            elif isinstance(val, bool):
                rec[col] = val
            elif isinstance(val, (int, float)) and pd.notna(val):
                rec[col] = val
            elif isinstance(val, str):
                rec[col] = val
            elif pd.notna(val):
                rec[col] = str(val)
        records.append(rec)
    return records


# -- public API -------------------------------------------------------------


def load_sample(
    connector: Any,
    txns: pd.DataFrame,
    accounts: pd.DataFrame | None = None,
    batch_size: int = 500,
) -> LoadReport:
    """Load accounts and transactions into Neo4j.

    Uses ``MERGE`` so rerunning is idempotent.  Never writes evaluation
    labels.  Returns a ``LoadReport`` with counts.
    """
    report = LoadReport()

    # -- accounts --
    if accounts is not None and "account_id" in accounts.columns:
        acct_records = _prepare_accounts(accounts)
        report.accounts_processed = len(acct_records)
        for i in range(0, len(acct_records), batch_size):
            batch = acct_records[i : i + batch_size]
            connector.execute_query(_MERGE_ACCOUNT, {"accounts": batch})
        report.accounts_created = report.accounts_processed  # MERGE: may match

    # -- transactions --
    clean, rej = _validate_txns(txns)
    report.rejected = rej
    report.transactions_processed = len(clean)
    txn_records = _prepare_txns(clean)
    for i in range(0, len(txn_records), batch_size):
        batch = txn_records[i : i + batch_size]
        connector.execute_query(_MERGE_TRANSFER, {"txns": batch})
    report.transactions_created = report.transactions_processed
    return report


def readback_counts(connector: Any) -> dict[str, int]:
    """Return node and relationship counts for verification."""
    with connector.session() as s:
        nodes = s.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = s.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
    return {"nodes": int(nodes), "relationships": int(rels)}

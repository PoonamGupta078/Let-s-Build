"""Build a directed multi-edge transaction graph from validated transaction data.

Each transaction becomes one directed edge. Parallel edges between the same
accounts are preserved (NetworkX MultiDiGraph, key = txn_id).

Policies
--------
Missing account references: when an accounts DataFrame is provided, any
    src/dst account not found in it is recorded in ``missing_accounts`` but
    the transaction is still added to the graph — nothing is silently dropped.

Self-transfers: preserved as self-loop edges. Whether self-transfers should
    appear in the input is an ingestion/validation concern (see
    ``ValidationPolicy.reject_self_transfers``), not a graph-construction one.

Label leakage: only columns from the documented internal schema
    (INTERNAL_TXN_COLUMNS + CURRENCY_COLUMN) are propagated as edge
    attributes. Extra columns — including any laundering labels — are ignored.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx
import pandas as pd

from ingestion.schema import CURRENCY_COLUMN, INTERNAL_TXN_COLUMNS

# Columns that may appear as edge attributes (subset of possible input columns).
_EDGE_ATTR_COLUMNS = [
    "txn_id", "ts", "amount", "type", "channel", "ext_bank", "currency",
]


@dataclass
class GraphBuildResult:
    """Return value of :func:`build_graph`."""

    graph: nx.MultiDiGraph
    missing_accounts: set[str] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)


def build_graph(
    txns: pd.DataFrame,
    accounts: pd.DataFrame | None = None,
) -> GraphBuildResult:
    """Build a MultiDiGraph from a validated transaction DataFrame.

    Parameters
    ----------
    txns
        Internal-schema frame (at minimum: txn_id, ts, src, dst, amount).
    accounts
        Optional account metadata (must contain ``account_id``).  When
        provided, node attributes are added and missing references are
        reported.
    """
    required = {"txn_id", "ts", "src", "dst", "amount"}
    missing_cols = required - set(txns.columns)
    if missing_cols:
        raise ValueError(f"input missing required columns: {sorted(missing_cols)}")

    warnings: list[str] = []
    txns_clean = txns.copy()

    # Drop rows with blank src or dst (report, don't silently discard).
    blank_mask = txns_clean["src"].isna() | txns_clean["dst"].isna()
    if blank_mask.any():
        n = int(blank_mask.sum())
        warnings.append(f"{n} transaction(s) with missing src/dst dropped from graph")
        txns_clean = txns_clean.loc[~blank_mask]

    # Accounts present in the transaction data.
    all_accounts: set[str] = set(
        txns_clean["src"].astype(str).unique()
    ) | set(txns_clean["dst"].astype(str).unique())

    # Account metadata lookup.
    account_set: set[str] = set()
    account_rows: dict[str, dict] = {}
    if accounts is not None and "account_id" in accounts.columns:
        account_set = set(accounts["account_id"].astype(str))
        for _, row in accounts.iterrows():
            aid = str(row["account_id"])
            attrs = {
                k: v for k, v in row.items()
                if k != "account_id" and pd.notna(v)
            }
            account_rows[aid] = {k: str(v) if isinstance(v, str) else v for k, v in attrs.items()}
    elif accounts is not None:
        warnings.append(
            "accounts DataFrame provided but has no 'account_id' column; "
            "node metadata and missing-reference check skipped"
        )

    missing_accounts = all_accounts - account_set if account_set else set()

    G = nx.MultiDiGraph()

    # Add nodes — with metadata when available, bare otherwise.
    for acct in all_accounts:
        if acct in account_rows:
            G.add_node(acct, **account_rows[acct])
        else:
            G.add_node(acct)

    # Only propagate schema-approved columns as edge attributes.
    attr_cols = [c for c in _EDGE_ATTR_COLUMNS if c in txns_clean.columns]

    for row in txns_clean.itertuples(index=False):
        src, dst = str(row.src), str(row.dst)
        key = row.txn_id if pd.notna(row.txn_id) else None
        attrs: dict = {}
        for col in attr_cols:
            val = getattr(row, col)
            if pd.notna(val):
                attrs[col] = val
        G.add_edge(src, dst, key=key, **attrs)

    return GraphBuildResult(graph=G, missing_accounts=missing_accounts, warnings=warnings)
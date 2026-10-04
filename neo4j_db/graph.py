"""Read the transaction graph back from Neo4j.

Complements neo4j_db/loader.py (which writes). These functions are read-only:
they never create, update, or delete data.
"""
from __future__ import annotations

from typing import Any


def read_graph(
    connector: Any,
    account_ids: set[str],
) -> tuple[list[dict], list[dict]]:
    """Return (node_rows, edge_rows) for the given accounts.

    node_rows: ``[{ "id": ... }]``
    edge_rows: ``[{ "txn_id", "source", "target", "amount", "ts", "channel" }]``
    """
    ids = sorted(account_ids)
    with connector.session() as session:
        node_rows = session.run(
            "MATCH (a:Account) WHERE a.account_id IN $ids "
            "RETURN a.account_id AS id",
            ids=ids,
        ).data()
        edge_rows = session.run(
            "MATCH (a:Account)-[r:TRANSFER]->(b:Account) "
            "WHERE a.account_id IN $ids AND b.account_id IN $ids "
            "RETURN r.txn_id AS txn_id, a.account_id AS source, "
            "b.account_id AS target, r.amount AS amount, "
            "toString(r.ts) AS ts, r.channel AS channel",
            ids=ids,
        ).data()
    return node_rows, edge_rows

"""Neo4j connectivity and sample-load check.

Usage: python scripts/neo4j_check.py

Requires NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in the environment (or .env).
If not configured, reports the issue clearly and exits without error.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd

from neo4j_db.connector import Neo4jConnector, Neo4jSettings
from neo4j_db.loader import load_sample, readback_counts


def main() -> int:
    settings = Neo4jSettings.from_env()
    if not settings.is_configured:
        print("SKIP: Neo4j is not configured.")
        print("  Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in a .env file.")
        print("  See .env.example for the expected variables.")
        return 1

    print(f"Connecting to {settings.uri} as {settings.user} ...")
    try:
        conn = Neo4jConnector(settings)
    except Exception as exc:
        print(f"FAIL: could not create driver: {exc}")
        return 1

    try:
        info = conn.verify_connectivity()
        print(f"OK: connected.  Server version: {info['server_version']}")

        print("Ensuring constraints ...")
        for msg in conn.ensure_schema():
            print(f"  {msg}")

        T0 = pd.Timestamp("2022-09-01 10:00")
        test_txns = pd.DataFrame([
            {"txn_id": "_check_t1", "ts": T0, "src": "_check_A", "dst": "_check_B",
             "amount": 1.0, "type": "transfer", "channel": "test",
             "ext_bank": False, "currency": "USD"},
        ])
        test_accounts = pd.DataFrame(
            [{"account_id": "_check_A"}, {"account_id": "_check_B"}]
        )

        report = load_sample(conn, test_txns, test_accounts)
        print(f"Loaded {report.accounts_processed} accounts, "
              f"{report.transactions_processed} txns.  Rejected: {report.rejected}.")

        counts = readback_counts(conn)
        print(f"Readback: {counts['nodes']} nodes, {counts['relationships']} rels.")
        assert counts["nodes"] >= 2
        assert counts["relationships"] >= 1
        print("OK: readback verified.")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    finally:
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    sys.exit(main())
# placeholder 

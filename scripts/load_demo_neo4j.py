"""Load the synthetic demo case into Neo4j (idempotent).

Usage: python scripts/load_demo_neo4j.py

Requires NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD in the environment (or .env).
Uses MERGE, so rerunning is safe and does not create duplicates. It adds only
the 4 demo accounts (S, M1, M2, CASH) and their 4 transfers; existing data is
left untouched.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.make_case import make_case  # noqa: E402
from neo4j_db.connector import Neo4jConnector, Neo4jSettings  # noqa: E402
from neo4j_db.loader import load_sample, readback_counts  # noqa: E402


def main() -> int:
    settings = Neo4jSettings.from_env()
    if not settings.is_configured:
        print("SKIP: Neo4j is not configured.")
        print("  Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD (see .env.example).")
        return 1

    case = make_case(seed=42, background_rows=0)
    try:
        connector = Neo4jConnector(settings)
    except Exception as exc:
        print(f"FAIL: could not connect to Neo4j: {exc}")
        return 1

    try:
        for message in connector.ensure_schema():
            print(f"  {message}")
        report = load_sample(connector, case.transactions, case.accounts)
        counts = readback_counts(connector)
        print(f"Loaded demo case: {report.accounts_processed} accounts, "
              f"{report.transactions_processed} transactions.")
        print(f"Neo4j now holds {counts['nodes']} nodes and "
              f"{counts['relationships']} relationships.")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1
    finally:
        connector.close()


if __name__ == "__main__":
    sys.exit(main())

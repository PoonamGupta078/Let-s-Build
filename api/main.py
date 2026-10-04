"""SecureTrace FastAPI backend.

Read-only wrappers over the existing SEE / TRACE / CUT engines and the
transaction graph builder.  The demo endpoints operate on a deterministic
synthetic case (data/make_case.py) so the app runs without Neo4j, credentials,
or the full 4.5M-row IBM dataset.

No endpoint executes a freeze or writes to any database.  All fund-flow
amounts are estimates (money is fungible); a human investigator decides.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cut.run import recommend  # noqa: E402
from data.make_case import make_case  # noqa: E402
from graph.build import build_graph  # noqa: E402
from see.run import detect  # noqa: E402
from trace.config import TraceConfig  # noqa: E402
from trace.run import trace  # noqa: E402

from . import schemas  # noqa: E402

# Deterministic synthetic demo case (currency-agnostic, no 'currency' column).
_DEMO_CASE = make_case(seed=42, background_rows=0)
_SEED_ACCOUNT, (_SEED_TS, _SEED_AMOUNT) = next(iter(_DEMO_CASE.seeds.items()))
_EXITS = _DEMO_CASE.exits
_DEMO_ALERTS = detect(_DEMO_CASE.transactions)

app = FastAPI(title="SecureTrace API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Local dev only: allow localhost / 127.0.0.1 / IPv6 ::1 on any port.
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=schemas.HealthOut)
def health() -> schemas.HealthOut:
    return schemas.HealthOut(
        status="ok",
        service="securetrace",
        version="0.1.0",
        demo_mode=True,
        data_source="make_case(seed=42, background_rows=0)",
    )


@app.get("/api/alerts", response_model=list[schemas.SeeAlertOut])
def alerts() -> list[schemas.SeeAlertOut]:
    """Run SEE detection on the demo case and return all alerts."""
    return [schemas.SeeAlertOut(**a.to_dict()) for a in _DEMO_ALERTS]


@app.get("/api/overview", response_model=schemas.OverviewOut)
def overview() -> schemas.OverviewOut:
    """Dashboard summary counts derived from the synthetic demo case."""
    return schemas.OverviewOut(
        demo=True,
        data_source="make_case(seed=42, background_rows=0)",
        accounts=len(_DEMO_CASE.accounts),
        transactions=len(_DEMO_CASE.transactions),
        alerts=len(_DEMO_ALERTS),
        rule_distribution=dict(Counter(a.rule_id for a in _DEMO_ALERTS)),
        exits=len(_DEMO_CASE.exits),
        seed_accounts=len(_DEMO_CASE.seeds),
    )


def _in_memory_graph() -> schemas.GraphOut:
    """Fallback: build the transaction graph in-memory (no Neo4j required)."""
    result = build_graph(_DEMO_CASE.transactions, _DEMO_CASE.accounts)
    g = result.graph
    nodes = [
        schemas.GraphNodeOut(
            id=str(node),
            role=data.get("role"),
            is_exit=bool(data.get("is_exit", False)),
        )
        for node, data in g.nodes(data=True)
    ]
    edges = [
        schemas.GraphEdgeOut(
            txn_id=str(key),
            source=str(source),
            target=str(target),
            amount=float(data["amount"]),
            ts=str(data["ts"]),
            channel=data.get("channel"),
            type=data.get("type"),
        )
        for source, target, key, data in g.edges(data=True, keys=True)
    ]
    return schemas.GraphOut(nodes=nodes, edges=edges, demo=True)


def _neo4j_graph() -> schemas.GraphOut | None:
    """Read the demo-case graph from Neo4j; return None if unavailable/empty."""
    try:
        from neo4j_db.connector import Neo4jConnector, Neo4jSettings
        from neo4j_db.graph import read_graph

        settings = Neo4jSettings.from_env()
        if not settings.is_configured:
            return None
        connector = Neo4jConnector(settings)
    except Exception:
        return None

    try:
        account_ids = {str(a) for a in _DEMO_CASE.accounts["account_id"]}
        node_rows, edge_rows = read_graph(connector, account_ids)
        if not node_rows and not edge_rows:
            # Demo case not loaded into Neo4j yet; fall back to in-memory.
            return None
        meta = {
            str(row.account_id): (str(row.role), bool(row.is_exit))
            for row in _DEMO_CASE.accounts.itertuples(index=False)
        }
        nodes = [
            schemas.GraphNodeOut(
                id=row["id"],
                role=meta.get(row["id"], (None, False))[0],
                is_exit=meta.get(row["id"], (None, False))[1],
            )
            for row in node_rows
        ]
        edges = [
            schemas.GraphEdgeOut(
                txn_id=str(row["txn_id"]),
                source=row["source"],
                target=row["target"],
                amount=float(row["amount"]),
                ts=row["ts"],
                channel=row.get("channel"),
            )
            for row in edge_rows
        ]
        return schemas.GraphOut(nodes=nodes, edges=edges, demo=True)
    except Exception:
        return None
    finally:
        connector.close()


@app.get("/api/graph", response_model=schemas.GraphOut)
def graph() -> schemas.GraphOut:
    """Transaction graph — Neo4j-backed when available, else in-memory."""
    return _neo4j_graph() or _in_memory_graph()


@app.get("/api/trace", response_model=schemas.TraceOut)
def trace_endpoint(seed_account: str = "S") -> schemas.TraceOut:
    """TRACE estimated fund propagation from a demo seed account."""
    if seed_account not in _DEMO_CASE.seeds:
        raise HTTPException(
            status_code=404,
            detail=f"seed account {seed_account!r} not in the demo case",
        )
    result = trace(
        _DEMO_CASE.transactions,
        seed_account,
        _SEED_TS,
        _SEED_AMOUNT,
        config=TraceConfig(currency_mode="single"),  # demo case has no currency column
        exits=_EXITS,
    )
    return schemas.TraceOut(
        seed_account=result.seed_account,
        seed_amount=result.seed_amount,
        seed_currency=result.seed_currency,
        tainted_accounts=result.tainted_accounts,
        exit_taint_by_currency=result.exit_taint_by_currency,
        paths=[
            schemas.TracePathOut(
                endpoint=path.endpoint,
                endpoint_tainted=path.endpoint_tainted,
                currency=path.currency,
                steps=[
                    schemas.TraceStepOut(
                        txn_id=step.txn_id,
                        src=step.src,
                        dst=step.dst,
                        ts=step.ts,
                        amount=step.amount,
                        currency=step.currency,
                        tainted_amount=step.tainted_amount,
                        allocation_ratio=step.allocation_ratio,
                        reason=step.reason,
                    )
                    for step in path.steps
                ],
                greedy=path.greedy,
            )
            for path in result.paths
        ],
        disclaimer=result.disclaimer,
    )


@app.get("/api/cut", response_model=schemas.CutOut)
def cut_endpoint(
    seed_account: str = "S",
    t_alert: str = "2026-01-01 10:20:00",
) -> schemas.CutOut:
    """CUT advisory intervention recommendations for the demo case."""
    if seed_account not in _DEMO_CASE.seeds:
        raise HTTPException(
            status_code=404,
            detail=f"seed account {seed_account!r} not in the demo case",
        )
    result = recommend(
        _DEMO_CASE.transactions,
        _DEMO_CASE.seeds,
        _EXITS,
        pd.Timestamp(t_alert),
    )
    return schemas.CutOut(
        strategy=result.strategy,
        seed_accounts=list(result.seed_accounts),
        exit_accounts=list(result.exit_accounts),
        baseline_exit_taint=result.baseline_exit_taint,
        total_tainted_blocked=result.total_tainted_blocked,
        pct_blocked=result.pct_blocked,
        recommendations=[
            schemas.CutRecommendationOut(
                account=rec.account,
                rank=rec.rank,
                strategy=rec.strategy,
                evidence_txn_ids=list(rec.evidence_txn_ids),
                estimated_tainted_blocked=rec.estimated_tainted_blocked,
                estimated_clean_disrupted=rec.estimated_clean_disrupted,
                minutes_until_exit=rec.minutes_until_exit,
                rationale=rec.rationale,
                currency=rec.currency,
            )
            for rec in result.recommendations
        ],
        aggregate_clean_held=result.aggregate_clean_held,
        disclaimer=result.disclaimer,
    )

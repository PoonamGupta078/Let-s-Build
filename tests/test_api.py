"""Smoke tests for the FastAPI backend (api/main.py).

Uses fastapi.testclient.TestClient (httpx-backed, already a dependency).
These tests assert meaningful outcomes, not formatting.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["demo_mode"] is True


def test_alerts_returns_see_alerts():
    resp = client.get("/api/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    # The seeded two-mule case yields two rapid pass-through alerts.
    assert {a["account"] for a in alerts} == {"M1", "M2"}
    assert all(a["rule_id"] == "RPT001" for a in alerts)
    assert all(a["evidence_txn_ids"] for a in alerts)
    assert all(a["explanation"] for a in alerts)


def test_overview_returns_demo_counts():
    resp = client.get("/api/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo"] is True
    assert body["accounts"] == 4
    assert body["transactions"] == 4
    assert body["alerts"] == 2
    assert body["rule_distribution"] == {"RPT001": 2}
    assert body["seed_accounts"] == 1
    assert body["exits"] == 1


def test_graph_returns_case_nodes_and_edges():
    resp = client.get("/api/graph")
    assert resp.status_code == 200
    graph = resp.json()
    assert {n["id"] for n in graph["nodes"]} == {"S", "M1", "M2", "CASH"}
    assert len(graph["edges"]) == 4
    # Every edge carries a txn_id and amount.
    assert all(e["txn_id"] for e in graph["edges"])
    assert all(e["amount"] > 0 for e in graph["edges"])


def test_trace_returns_paths_and_taint():
    resp = client.get("/api/trace", params={"seed_account": "S"})
    assert resp.status_code == 200
    result = resp.json()
    assert result["seed_account"] == "S"
    assert len(result["paths"]) == 2
    assert "CASH" in result["tainted_accounts"]
    assert result["disclaimer"]


def test_trace_unknown_seed_404():
    resp = client.get("/api/trace", params={"seed_account": "NOPE"})
    assert resp.status_code == 404


def test_cut_returns_recommendations():
    resp = client.get(
        "/api/cut",
        params={"seed_account": "S", "t_alert": "2026-01-01T10:20:00"},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["strategy"] == "greedy"
    assert {rec["account"] for rec in result["recommendations"]} == {"M1", "M2"}
    assert result["pct_blocked"] == 100.0
    assert result["disclaimer"]

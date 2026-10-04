"""Milestone 2 tests: transaction graph construction and time-aware views.

Uses small synthetic fixtures; never loads the full IBM dataset.
"""
import pandas as pd
import pytest

from graph.build import GraphBuildResult, build_graph
from graph.views import case_subgraph, graph_as_of
from ingestion.schema import CURRENCY_COLUMN, INTERNAL_TXN_COLUMNS

T0 = pd.Timestamp("2022-09-01 10:00")
_m = pd.Timedelta

FIXTURE_TXNS = pd.DataFrame(
    [
        ("t1", T0 + _m(minutes=10), "A", "B", 100.0, "transfer", "NEFT", False, "US Dollar"),
        ("t2", T0 + _m(minutes=20), "B", "C", 50.0,  "transfer", "Wire",  True,  "Euro"),
        ("t3", T0 + _m(minutes=20), "B", "C", 30.0,  "transfer", "UPI",   True,  "Rupee"),
        ("t4", T0 + _m(minutes=30), "A", "A", 10.0,  "transfer", "NEFT",  False, "US Dollar"),
        ("t5", T0 + _m(minutes=40), "C", "D", 20.0,  "transfer", "Cheque", False, "US Dollar"),
        ("t6", T0 + _m(minutes=100),"A", "B", 999.0, "transfer", "NEFT",  False, "US Dollar"),
    ],
    columns=INTERNAL_TXN_COLUMNS + [CURRENCY_COLUMN],
)

FIXTURE_ACCOUNTS = pd.DataFrame(
    [("A", "SOURCE", False), ("B", "MULE", False), ("C", "NORMAL", False)],
    columns=["account_id", "role", "is_exit"],
)


# --- graph construction ---


def test_directed_edge_orientation():
    result = build_graph(FIXTURE_TXNS)
    G = result.graph
    assert G.has_edge("A", "B")
    assert not G.has_edge("B", "A")


def test_parallel_transactions_preserved():
    G = build_graph(FIXTURE_TXNS).graph
    edges_bc = G.get_edge_data("B", "C")
    assert edges_bc is not None and len(edges_bc) == 2
    txn_ids = {d["txn_id"] for d in edges_bc.values()}
    assert txn_ids == {"t2", "t3"}


def test_edge_attributes_preserved():
    G = build_graph(FIXTURE_TXNS).graph
    data = G.edges["A", "B", "t1"]
    assert data["txn_id"] == "t1"
    assert data["ts"] == T0 + _m(minutes=10)
    assert data["amount"] == 100.0
    assert data["currency"] == "US Dollar"
    assert data["channel"] == "NEFT"


def test_self_transfer_creates_self_loop():
    G = build_graph(FIXTURE_TXNS).graph
    assert G.has_edge("A", "A")
    self_edges = G.get_edge_data("A", "A")
    assert len(self_edges) == 1
    assert self_edges["t4"]["txn_id"] == "t4"


def test_missing_account_references_detected():
    result = build_graph(FIXTURE_TXNS, FIXTURE_ACCOUNTS)
    assert isinstance(result, GraphBuildResult)
    assert "D" in result.missing_accounts
    assert result.graph.has_node("D")
    assert result.graph.has_edge("C", "D")  # transaction preserved
    assert result.graph.nodes["A"]["role"] == "SOURCE"


def test_node_attributes_from_accounts():
    result = build_graph(FIXTURE_TXNS, FIXTURE_ACCOUNTS)
    assert result.graph.nodes["A"]["role"] == "SOURCE"
    assert result.graph.nodes["B"]["role"] == "MULE"
    assert result.graph.nodes["C"]["role"] == "NORMAL"
    assert "role" not in result.graph.nodes.get("D", {})


# --- cutoff views ---


CUTOFF = T0 + _m(minutes=50)


def test_inclusive_cutoff():
    view = graph_as_of(build_graph(FIXTURE_TXNS).graph, CUTOFF)
    assert view.number_of_edges() == 5  # t1..t5
    for _, _, data in view.edges(data=True):
        assert data["ts"] <= CUTOFF


def test_future_transactions_excluded():
    view = graph_as_of(build_graph(FIXTURE_TXNS).graph, CUTOFF)
    txn_ids = {d["txn_id"] for _, _, d in view.edges(data=True)}
    assert "t6" not in txn_ids


def test_original_graph_unchanged_by_view():
    G = build_graph(FIXTURE_TXNS).graph
    original_edges = G.number_of_edges()
    original_nodes = G.number_of_nodes()
    _ = graph_as_of(G, T0 + _m(minutes=5))
    assert G.number_of_edges() == original_edges
    assert G.number_of_nodes() == original_nodes


def test_view_preserves_parallel_edges_and_attrs():
    view = graph_as_of(build_graph(FIXTURE_TXNS).graph, CUTOFF)
    edges_bc = view.get_edge_data("B", "C")
    assert edges_bc is not None and len(edges_bc) == 2
    assert edges_bc["t2"]["currency"] == "Euro"
    assert edges_bc["t3"]["currency"] == "Rupee"


# --- case subgraph ---


def test_case_subgraph_deterministic_and_correct():
    G = build_graph(FIXTURE_TXNS).graph
    sg1 = case_subgraph(G, {"A", "B"})
    sg2 = case_subgraph(G, {"A", "B"})
    assert sg1.number_of_edges() == sg2.number_of_edges()
    # t1 A→B, t4 A→A, t6 A→B — all have both endpoints in {A, B}
    assert sg1.number_of_edges() == 3
    assert sg1.has_edge("A", "B")
    assert sg1.has_edge("A", "A")
    assert not sg1.has_edge("B", "C")
    # parallel A→B edges preserved (t1 and t6)
    assert len(sg1.get_edge_data("A", "B")) == 2


# --- label leakage ---


def test_labels_cannot_enter_graph():
    """build_graph ignores extra columns (including labels) and never exposes
    them as edge or node attributes."""
    txns_with_label = FIXTURE_TXNS.copy()
    txns_with_label["is_laundering"] = [1, 0, 0, 0, 0, 0]
    G = build_graph(txns_with_label).graph
    for _, _, data in G.edges(data=True):
        assert "is_laundering" not in data
        assert "label" not in data
    for _, data in G.nodes(data=True):
        assert "is_laundering" not in data


# --- edge cases ---


def test_empty_input():
    empty = pd.DataFrame(columns=INTERNAL_TXN_COLUMNS + [CURRENCY_COLUMN])
    result = build_graph(empty)
    assert result.graph.number_of_nodes() == 0
    assert result.graph.number_of_edges() == 0
    assert result.missing_accounts == set()


def test_invalid_cutoff_raises():
    G = build_graph(FIXTURE_TXNS).graph
    with pytest.raises(ValueError):
        graph_as_of(G, pd.NaT)
    with pytest.raises(ValueError):
        graph_as_of(G, "not-a-timestamp")
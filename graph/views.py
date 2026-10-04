"""Time-aware and account-filtered graph views.

All views return a NEW MultiDiGraph; the input graph is never mutated.
"""
from __future__ import annotations

import networkx as nx
import pandas as pd


def graph_as_of(G: nx.MultiDiGraph, cutoff: pd.Timestamp) -> nx.MultiDiGraph:
    """Return the subgraph of edges with ``ts <= cutoff`` (inclusive).

    Nodes that have no remaining edges are excluded.  Node attributes from
    the original graph are preserved for surviving nodes.
    """
    if not isinstance(cutoff, pd.Timestamp) or pd.isna(cutoff):
        raise ValueError(f"cutoff must be a valid pd.Timestamp, got {cutoff!r}")

    H = nx.MultiDiGraph()
    for u, v, key, data in G.edges(data=True, keys=True):
        if data["ts"] <= cutoff:
            H.add_edge(u, v, key=key, **data)

    # Carry over node attributes for surviving nodes.
    for node in H.nodes():
        if node in G.nodes:
            H.nodes[node].update(G.nodes[node])
    return H


def case_subgraph(G: nx.MultiDiGraph, accounts: set) -> nx.MultiDiGraph:
    """Return the subgraph of edges where BOTH endpoints are in *accounts*.

    Deterministic: same input graph and account set always produce the same
    result.  Node attributes are preserved for included nodes.
    """
    H = nx.MultiDiGraph()
    for u, v, key, data in G.edges(data=True, keys=True):
        if u in accounts and v in accounts:
            H.add_edge(u, v, key=key, **data)

    for node in H.nodes():
        if node in G.nodes:
            H.nodes[node].update(G.nodes[node])
    return H
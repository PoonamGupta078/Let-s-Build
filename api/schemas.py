"""Pydantic response schemas for the SecureTrace API.

These mirror the existing SEE/TRACE/CUT result models (see/models.py,
trace/models.py, cut/models.py) and the transaction graph (graph/build.py).
All amounts are estimated; every collection of alerts/traces/cuts carries a
disclaimer from the underlying engine.
"""
from __future__ import annotations

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    service: str
    version: str
    demo_mode: bool
    data_source: str


class OverviewOut(BaseModel):
    demo: bool
    data_source: str
    accounts: int
    transactions: int
    alerts: int
    rule_distribution: dict[str, int]
    exits: int
    seed_accounts: int


class SeeAlertOut(BaseModel):
    alert_id: str
    rule_id: str
    rule_name: str
    account: str
    score: int
    window_start: str
    window_end: str
    evidence_txn_ids: list[str]
    explanation: str
    disclaimer: str


class GraphNodeOut(BaseModel):
    id: str
    role: str | None = None
    is_exit: bool = False


class GraphEdgeOut(BaseModel):
    txn_id: str
    source: str
    target: str
    amount: float
    ts: str
    channel: str | None = None
    type: str | None = None


class GraphOut(BaseModel):
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]
    demo: bool = True


class TraceStepOut(BaseModel):
    txn_id: str
    src: str
    dst: str
    ts: str
    amount: float
    currency: str
    tainted_amount: float
    allocation_ratio: float
    reason: str


class TracePathOut(BaseModel):
    endpoint: str
    endpoint_tainted: float
    currency: str
    steps: list[TraceStepOut]
    greedy: bool


class TraceOut(BaseModel):
    seed_account: str
    seed_amount: float
    seed_currency: str
    tainted_accounts: dict[str, dict[str, float]]
    exit_taint_by_currency: dict[str, float]
    paths: list[TracePathOut]
    disclaimer: str


class CutRecommendationOut(BaseModel):
    account: str
    rank: int | None
    strategy: str
    evidence_txn_ids: list[str]
    estimated_tainted_blocked: float | None
    estimated_clean_disrupted: float | None
    minutes_until_exit: float | None
    rationale: str
    currency: str


class CutOut(BaseModel):
    strategy: str
    seed_accounts: list[str]
    exit_accounts: list[str]
    baseline_exit_taint: float
    total_tainted_blocked: float
    pct_blocked: float | None
    recommendations: list[CutRecommendationOut]
    aggregate_clean_held: float | None
    disclaimer: str

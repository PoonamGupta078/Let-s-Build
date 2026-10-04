"""TRACE data models: structured, serializable output."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class TraceStep:
    """One hop in a provenance path."""

    txn_id: str
    src: str
    dst: str
    ts: str
    amount: float
    currency: str
    tainted_amount: float
    allocation_ratio: float
    reason: str


@dataclass(frozen=True)
class TracePath:
    """One provenance path from seed to an endpoint."""

    endpoint: str
    endpoint_tainted: float
    currency: str
    steps: tuple[TraceStep, ...]


@dataclass(frozen=True)
class TraceResult:
    """Complete TRACE output for one seed."""

    alert_id: str
    seed_account: str
    seed_amount: float
    seed_currency: str
    seed_ts: str
    config: dict
    tainted_accounts: dict[str, float]
    tainted_edges: dict[str, float]
    paths: tuple[TracePath, ...]
    disclaimer: str = (
        "Taint estimates are investigative leads. Money is fungible; "
        "these proportions do not prove that specific funds were laundered."
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        d["paths"] = [
            {**p, "steps": [asdict(s) for s in p["steps"]]}
            for p in d["paths"]
        ]
        return d

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, **kwargs)
 

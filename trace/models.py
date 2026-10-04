"""TRACE data models: structured, serializable output.

All models are frozen dataclasses.  ``to_dict()`` and ``to_json()`` produce
deterministic, JSON-safe output without relying on ``default=str``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class TraceStep:
    """One hop in a provenance path.

    ``tainted_amount`` is the estimated suspicious portion of this transaction.
    ``amount`` is the full transaction amount.  The two are distinct.
    ``allocation_ratio`` is the fraction of this transaction's amount
    estimated as tainted (``tainted_amount / amount``).
    """

    txn_id: str
    src: str
    dst: str
    ts: str          # ISO timestamp
    amount: float    # full transaction amount
    currency: str
    tainted_amount: float  # estimated suspicious portion
    allocation_ratio: float
    reason: str      # "seed" or "propagated from {src}"


@dataclass(frozen=True)
class TracePath:
    """One greedy provenance path from seed to an endpoint.

    ``greedy=True`` indicates the path was built by ``core.taint.top_paths``,
    which selects the largest earlier tainted inflow at each step.  This is
    a heuristic, not a globally optimal trace.
    """

    endpoint: str
    endpoint_tainted: float
    currency: str
    steps: tuple[TraceStep, ...]
    greedy: bool = True


@dataclass(frozen=True)
class TraceResult:
    """Complete TRACE output for one seed.

    ``tainted_accounts`` maps ``account -> {currency: amount}`` so that
    amounts are never summed across currencies.

    ``exit_taint_by_currency`` maps ``{currency: total_tainted}`` for the
    requested exit accounts only.  Empty when no exits are provided.

    ``disclaimer`` is fixed text stating that taint estimates are
    investigative leads under a stated accounting policy, not proof that
    specific physical funds moved.
    """

    alert_id: str
    seed_account: str
    seed_amount: float
    seed_currency: str
    seed_ts: str
    config: dict
    tainted_accounts: dict[str, dict[str, float]]
    tainted_edges: dict[str, float]
    exit_taint_by_currency: dict[str, float]
    paths: tuple[TracePath, ...]
    disclaimer: str = (
        "Taint estimates are investigative leads. Money is fungible; "
        "these proportions are estimates under a stated accounting policy, "
        "not proof that specific physical funds moved or that an account "
        "committed a crime."
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        # asdict converts frozen dataclass tuples to lists; restore paths
        # structure explicitly for correct JSON serialization.
        d["paths"] = [
            {**p, "steps": [asdict(s) for s in p["steps"]]}
            if isinstance(p.get("steps"), tuple)
            else {**p, "steps": [asdict(s) if hasattr(s, "__dataclass_fields__") else s
                                  for s in p["steps"]]}
            for p in d["paths"]
        ]
        return d

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, **kwargs)
 

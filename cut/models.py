"""CUT data models: structured, serializable advisory output.

All models are frozen dataclasses.  ``to_dict()`` and ``to_json()`` produce
deterministic, JSON-safe output.  Fields that are unavailable for a given
strategy are ``None`` rather than fabricated values.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math


@dataclass(frozen=True)
class CutRecommendation:
    """One advisory recommendation for an account.

    Fields that are unavailable for the ``block_all`` strategy (which
    produces an unranked cut-set) are set to ``None``.
    """

    account: str
    rank: int | None          # None for block_all (unranked cut-set)
    strategy: str             # "greedy" or "block_all"
    evidence_txn_ids: tuple[str, ...]
    estimated_tainted_blocked: float | None
    estimated_clean_disrupted: float | None
    minutes_until_exit: float | None
    rationale: str
    currency: str             # currency of this recommendation


@dataclass(frozen=True)
class CutResult:
    """Complete CUT output for one seed/exits pair.

    ``pct_blocked`` is ``None`` when the baseline exit taint is zero,
    avoiding a meaningless 0/0 division.

    ``aggregate_clean_held`` is populated only for ``block_all`` (where
    the per-account breakdown is unavailable) and represents the total
    clean volume held across all accounts in the cut-set.

    ``disclaimer`` is fixed advisory text: no holds are executed.
    """

    strategy: str
    seed_accounts: tuple[str, ...]
    exit_accounts: tuple[str, ...]
    baseline_exit_taint: float
    total_tainted_blocked: float
    pct_blocked: float | None
    recommendations: tuple[CutRecommendation, ...]
    config: dict
    aggregate_clean_held: float | None = None
    disclaimer: str = (
        "These are advisory recommendations only. No holds have been placed. "
        "All amounts are estimates. The investigator makes the final decision."
    )

    def to_dict(self) -> dict:
        d = asdict(self)
        # Ensure NaN is not present (JSON-unsafe); convert to None.
        if d["pct_blocked"] is not None and (math.isnan(d["pct_blocked"]) or math.isinf(d["pct_blocked"])):
            d["pct_blocked"] = None
        if d["aggregate_clean_held"] is not None and (
            math.isnan(d["aggregate_clean_held"]) or math.isinf(d["aggregate_clean_held"])
        ):
            d["aggregate_clean_held"] = None
        for rec in d["recommendations"]:
            for key in ("estimated_tainted_blocked", "estimated_clean_disrupted", "minutes_until_exit"):
                val = rec[key]
                if val is not None and (math.isnan(val) or math.isinf(val)):
                    rec[key] = None
        return d

    def to_json(self, **kwargs) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, **kwargs)
"""CUT configuration."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CutConfig:
    """Configuration for CUT recommendation engine.

    Attributes
    ----------
    strategy : str
        ``"greedy"`` (default) uses core.freeze.plan() for ranked
        marginal-gain recommendations.  ``"block_all"`` uses
        core.freeze.block_all() for a minimum cut-set.
    max_recommendations : int
        Maximum number of accounts to recommend (greedy ``k``).
    hold_cost : float
        Disruption weight in greedy scoring.
    min_tainted_gain : float
        Minimum tainted reduction to accept a recommendation.
    block_all_hold_cost : float
        Hold-cost parameter for the block_all strategy.
    min_tainted_threshold : float
        Accounts with tainted amount below this are excluded.
    """

    strategy: str = "greedy"
    max_recommendations: int = 5
    hold_cost: float = 0.0
    min_tainted_gain: float = 1.0
    block_all_hold_cost: float = 1.0
    min_tainted_threshold: float = 1e-6

    def __post_init__(self) -> None:
        if self.strategy not in ("greedy", "block_all"):
            raise ValueError(
                f"strategy must be 'greedy' or 'block_all', got {self.strategy!r}"
            )
        if not isinstance(self.max_recommendations, int) or self.max_recommendations < 1:
            raise ValueError(
                f"max_recommendations must be an integer >= 1, got {self.max_recommendations!r}"
            )
        if not math.isfinite(self.hold_cost) or self.hold_cost < 0:
            raise ValueError(f"hold_cost must be finite and >= 0, got {self.hold_cost!r}")
        if not math.isfinite(self.min_tainted_gain) or self.min_tainted_gain < 0:
            raise ValueError(
                f"min_tainted_gain must be finite and >= 0, got {self.min_tainted_gain!r}"
            )
        if not math.isfinite(self.block_all_hold_cost) or self.block_all_hold_cost < 0:
            raise ValueError(
                f"block_all_hold_cost must be finite and >= 0, got {self.block_all_hold_cost!r}"
            )
        if not math.isfinite(self.min_tainted_threshold) or self.min_tainted_threshold < 0:
            raise ValueError(
                f"min_tainted_threshold must be finite and >= 0, got {self.min_tainted_threshold!r}"
            )
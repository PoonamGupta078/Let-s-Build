"""TRACE configuration."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TraceConfig:
    """Configuration for TRACE propagation.

    Attributes
    ----------
    currency_mode : str
        "per_currency" (default) propagates taint independently within each
        currency.  "single" treats all amounts as fungible across currencies.
    max_paths : int
        Maximum number of provenance paths to return.
    min_tainted_threshold : float
        Accounts with tainted amount below this are excluded from results.
    """

    currency_mode: str = "per_currency"
    max_paths: int = 10
    min_tainted_threshold: float = 1e-6

    def __post_init__(self) -> None:
        if self.currency_mode not in ("per_currency", "single"):
            raise ValueError(
                f"currency_mode must be 'per_currency' or 'single', "
                f"got {self.currency_mode!r}"
            )
        if self.max_paths < 1:
            raise ValueError(f"max_paths must be >= 1, got {self.max_paths}")
        if self.min_tainted_threshold < 0:
            raise ValueError(
                f"min_tainted_threshold must be >= 0, got {self.min_tainted_threshold}"
            )
 

"""ML experiment configuration."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class SplitConfig:
    """Chronological train/validation/test split boundaries.

    If train_end/val_end are None, boundaries are computed from the data
    at the 80th and 90th percentile timestamps.  If provided as ISO strings,
    they are used as-is.
    """
    train_end: str | None = None
    val_end: str | None = None

    def compute_boundaries(self, ts: pd.Series) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Return (train_end, val_end) from config or data percentiles."""
        ts_sorted = ts.sort_values().reset_index(drop=True)
        n = len(ts_sorted)
        if self.train_end is not None and self.val_end is not None:
            return pd.Timestamp(self.train_end), pd.Timestamp(self.val_end)
        # Percentile-based: 80th and 90th percentile timestamps
        train_end = ts_sorted.iloc[int(n * 0.80)]
        val_end = ts_sorted.iloc[int(n * 0.90)]
        return pd.Timestamp(train_end), pd.Timestamp(val_end)


@dataclass(frozen=True)
class FeatureConfig:
    """Feature engineering settings."""
    hist_window_hours: int = 24
    use_historical: bool = True


@dataclass(frozen=True)
class ExperimentConfig:
    split: SplitConfig = None
    features: FeatureConfig = None
    random_state: int = 42
    sample_size: int = 0  # 0 = full data

    def __post_init__(self):
        if self.split is None:
            object.__setattr__(self, 'split', SplitConfig())
        if self.features is None:
            object.__setattr__(self, 'features', FeatureConfig())
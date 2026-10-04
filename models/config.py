"""ML experiment configuration."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SplitConfig:
    """Chronological train/validation/test split boundaries (ISO timestamps)."""
    train_end: str = "2022-09-14 23:59:59"
    val_end:   str = "2022-09-16 23:59:59"


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
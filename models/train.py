"""Model training with leakage-safe pipelines."""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from time import perf_counter

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


def build_models(random_state: int = 42) -> dict:
    """Return baseline model dict. Keys are model names."""
    return {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "logistic": LogisticRegression(
            class_weight="balanced", max_iter=1000,
            solver="lbfgs", random_state=random_state,
        ),
        "hgb": HistGradientBoostingClassifier(
            class_weight="balanced", max_iter=200,
            learning_rate=0.1, max_depth=6,
            random_state=random_state, early_stopping=True,
            validation_fraction=0.1, n_iter_no_change=10,
        ),
    }


def train_and_predict(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
    X_test: np.ndarray, y_test: np.ndarray,
    feature_names: list[str],
    random_state: int = 42,
    output_dir: Path | None = None,
) -> dict:
    """Train all baseline models and return results dict.

    Each entry: {model_name: {metrics, model_path?, feature_names, ...}}
    """
    results = {}
    models = build_models(random_state)

    # Scale features for logistic regression (fit on train only)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    for name, model in models.items():
        t0 = perf_counter()

        # Use scaled features for logistic, raw for others
        if name == "logistic":
            model.fit(X_train_s, y_train)
            val_proba = model.predict_proba(X_val_s)[:, 1] if len(X_val_s) > 0 else np.array([])
            test_proba = model.predict_proba(X_test_s)[:, 1] if len(X_test_s) > 0 else np.array([])
        else:
            model.fit(X_train, y_train)
            val_proba = model.predict_proba(X_val)[:, 1] if len(X_val) > 0 else np.array([])
            test_proba = model.predict_proba(X_test)[:, 1] if len(X_test) > 0 else np.array([])

        train_time = perf_counter() - t0

        # Save model
        model_path = None
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            model_path = output_dir / f"{name}_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump({"model": model, "scaler": scaler if name == "logistic" else None}, f)

        results[name] = {
            "val_proba": val_proba,
            "test_proba": test_proba,
            "model_path": str(model_path) if model_path else None,
            "train_time_s": round(train_time, 2),
            "feature_names": feature_names,
            "n_features": len(feature_names),
        }

    return results
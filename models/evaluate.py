"""Evaluation metrics and threshold selection."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score,
    precision_recall_curve, precision_score, recall_score,
    roc_auc_score,
)


def select_threshold(y_val: np.ndarray, val_proba: np.ndarray) -> float:
    """Select threshold maximizing F1 on validation set."""
    precisions, recalls, thresholds = precision_recall_curve(y_val, val_proba)
    # Compute F1 for each threshold
    f1s = 2 * precisions[:-1] * recalls[:-1] / (precisions[:-1] + recalls[:-1] + 1e-10)
    best_idx = np.argmax(f1s)
    return float(thresholds[best_idx])


def compute_metrics(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> dict:
    """Compute all evaluation metrics at a given threshold."""
    if len(y_true) == 0 or len(proba) == 0:
        return {"threshold": round(threshold, 4), "precision": 0, "recall": 0, "f1": 0,
                "pr_auc": float("nan"), "roc_auc": float("nan"),
                "confusion_matrix": {"tn": 0, "fp": 0, "fn": 0, "tp": 0},
                "note": "empty split — no data to evaluate"}
    preds = (proba >= threshold).astype(int)
    prec = precision_score(y_true, preds, zero_division=0)
    rec = recall_score(y_true, preds, zero_division=0)
    f1 = f1_score(y_true, preds, zero_division=0)
    try:
        pr_auc = average_precision_score(y_true, proba)
    except ValueError:
        pr_auc = float("nan")
    try:
        roc = roc_auc_score(y_true, proba)
    except ValueError:
        roc = float("nan")
    cm = confusion_matrix(y_true, preds)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
    return {
        "threshold": round(threshold, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc, 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def evaluate_experiment(
    results: dict,
    y_val: np.ndarray,
    y_test: np.ndarray,
    split_sizes: dict,
    output_dir: Path | None = None,
) -> dict:
    """Evaluate all models and save report."""
    report = {"models": {}, "split_sizes": split_sizes}

    for name, res in results.items():
        val_proba = res["val_proba"]
        test_proba = res["test_proba"]

        # Select threshold on validation
        threshold = select_threshold(y_val, val_proba)

        val_metrics = compute_metrics(y_val, val_proba, threshold)
        test_metrics = compute_metrics(y_test, test_proba, threshold)

        report["models"][name] = {
            "val": val_metrics,
            "test": test_metrics,
            "train_time_s": res["train_time_s"],
            "model_path": res.get("model_path"),
            "n_features": res["n_features"],
        }

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "baseline_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

    return report
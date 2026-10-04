"""Tests for ML pipeline — training, evaluation, and GNN forward pass."""
import numpy as np
import pandas as pd
import pytest

from models.config import ExperimentConfig
from models.train import build_models, train_and_predict
from models.evaluate import compute_metrics, select_threshold
from models.gnn import GCN
from scipy import sparse


def test_dummy_classifier():
    models = build_models(42)
    assert "dummy" in models
    assert "logistic" in models
    assert "hgb" in models


def test_train_and_predict_shapes():
    rng = np.random.default_rng(42)
    X_train = rng.normal(0, 1, (100, 5))
    y_train = rng.integers(0, 2, 100)
    X_val = rng.normal(0, 1, (20, 5))
    y_val = rng.integers(0, 2, 20)
    X_test = rng.normal(0, 1, (20, 5))
    y_test = rng.integers(0, 2, 20)

    results = train_and_predict(X_train, y_train, X_val, y_val, X_test, y_test,
                                ["f1", "f2", "f3", "f4", "f5"], 42)
    for name in ["dummy", "logistic", "hgb"]:
        assert name in results
        assert results[name]["val_proba"].shape == (20,)
        assert results[name]["test_proba"].shape == (20,)
        assert results[name]["train_time_s"] >= 0


def test_select_threshold():
    y_val = np.array([0, 0, 0, 1, 1, 1])
    proba = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    thr = select_threshold(y_val, proba)
    assert 0.0 <= thr <= 1.0


def test_compute_metrics_range():
    y_true = np.array([0, 0, 0, 1, 1])
    proba = np.array([0.1, 0.2, 0.3, 0.8, 0.9])
    metrics = compute_metrics(y_true, proba, 0.5)
    assert 0 <= metrics["precision"] <= 1
    assert 0 <= metrics["recall"] <= 1
    assert 0 <= metrics["f1"] <= 1
    assert 0 <= metrics["pr_auc"] <= 1
    assert metrics["confusion_matrix"]["tp"] + metrics["confusion_matrix"]["fn"] == 2


def test_gnn_forward_shapes():
    rng = np.random.default_rng(42)
    n_nodes = 10
    node_feat = rng.normal(0, 1, (n_nodes, 3)).astype(np.float32)
    # Simple adjacency
    A = sparse.csr_matrix((np.ones(5), ([0,1,2,3,4], [1,2,3,4,5])), shape=(n_nodes, n_nodes))
    A = A + A.T
    A.setdiag(1)
    d = np.array(A.sum(axis=1)).ravel()
    D_inv = sparse.diags(1.0 / np.sqrt(d + 1e-10))
    A_norm = D_inv @ A @ D_inv

    gcn = GCN(node_feat_dim=3, edge_feat_dim=3, hidden_dim=8, epochs=2, seed=42)
    src_idx = np.array([0, 1, 2])
    dst_idx = np.array([1, 2, 3])
    edge_feat = rng.normal(0, 1, (3, 3)).astype(np.float32)
    y = np.array([0.0, 1.0, 0.0])

    loss = gcn.train_step(node_feat, A_norm, src_idx, dst_idx, edge_feat, y)
    assert np.isfinite(loss)
    probs = gcn.predict(node_feat, A_norm, src_idx, dst_idx, edge_feat)
    assert probs.shape == (3,)
    assert all(0 <= p <= 1 for p in probs)


def test_gnn_deterministic():
    rng = np.random.default_rng(42)
    n = 5
    nf = rng.normal(0, 1, (n, 3)).astype(np.float32)
    A = sparse.eye(n, format="csr", dtype=np.float32)
    src = np.array([0, 1])
    dst = np.array([1, 2])
    ef = rng.normal(0, 1, (2, 3)).astype(np.float32)
    y = np.array([0.0, 1.0])

    gcn1 = GCN(node_feat_dim=3, edge_feat_dim=3, hidden_dim=4, epochs=5, seed=99)
    gcn2 = GCN(node_feat_dim=3, edge_feat_dim=3, hidden_dim=4, epochs=5, seed=99)
    gcn1.train_step(nf, A, src, dst, ef, y)
    gcn2.train_step(nf, A, src, dst, ef, y)
    np.testing.assert_array_equal(gcn1.W_clf, gcn2.W_clf)


def test_gnn_class_weighted():
    """GNN with class weights should handle severe imbalance without crashing."""
    rng = np.random.default_rng(42)
    n = 20
    nf = rng.normal(0, 1, (n, 3)).astype(np.float32)
    A = sparse.eye(n, format="csr", dtype=np.float32)
    src = np.arange(19)
    dst = np.arange(1, 20)
    ef = rng.normal(0, 1, (19, 3)).astype(np.float32)
    y = np.zeros(19, dtype=np.float32)
    y[0] = 1.0  # 1 positive out of 19

    gcn = GCN(node_feat_dim=3, edge_feat_dim=3, hidden_dim=8, epochs=5, seed=42)
    # Compute weights like the real pipeline
    pos_w = 18.0 / 1.0
    sw = np.where(y == 1, pos_w, 1.0)
    loss = gcn.train_step(nf, A, src, dst, ef, y, sw)
    assert np.isfinite(loss)
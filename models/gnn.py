"""Lightweight GCN for transaction classification (numpy, no PyTorch).

Implements a 2-layer Graph Convolutional Network using sparse matrix
operations.  Designed for sampled subgraphs (bounded memory).
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy import sparse


class GCNLayer:
    """Single GCN layer: H' = relu(A_norm @ H @ W)."""

    def __init__(self, in_dim: int, out_dim: int, rng: np.random.Generator):
        # Xavier initialization
        scale = np.sqrt(2.0 / (in_dim + out_dim))
        self.W = rng.normal(0, scale, (in_dim, out_dim)).astype(np.float32)
        self.b = np.zeros(out_dim, dtype=np.float32)
        self.dW = None
        self.db = None

    def forward(self, H: np.ndarray, A_norm: sparse.csr_matrix) -> np.ndarray:
        self._H = H
        self._A_norm = A_norm
        Z = A_norm @ H @ self.W + self.b
        self._Z = Z
        self._A = np.maximum(Z, 0)  # ReLU
        return self._A

    def backward(self, d_out: np.ndarray, lr: float):
        # d_out is gradient w.r.t. ReLU output
        d_z = d_out * (self._Z > 0).astype(np.float32)
        self.dW = self._H.T @ (self._A_norm.T @ d_z)
        self.db = d_z.sum(axis=0)
        d_h = (self._A_norm @ d_z) @ self.W.T
        self.W -= lr * self.dW
        self.b -= lr * self.db
        return d_h


class GCN:
    """2-layer GCN for node embedding, combined with edge features for
    transaction-level classification."""

    def __init__(
        self,
        node_feat_dim: int,
        edge_feat_dim: int,
        hidden_dim: int = 32,
        lr: float = 0.01,
        epochs: int = 50,
        seed: int = 42,
    ):
        rng = np.random.default_rng(seed)
        self.hidden_dim = hidden_dim
        self.lr = lr
        self.epochs = epochs
        self.layer1 = GCNLayer(node_feat_dim, hidden_dim, rng)
        self.layer2 = GCNLayer(hidden_dim, hidden_dim, rng)
        self.edge_feat_dim = edge_feat_dim
        # Classifier: [src_emb, dst_emb, edge_feat] -> sigmoid
        in_dim = hidden_dim * 2 + edge_feat_dim
        scale = np.sqrt(2.0 / in_dim)
        self.W_clf = rng.normal(0, scale, (in_dim, 1)).astype(np.float32)
        self.b_clf = np.zeros(1, dtype=np.float32)

    def _sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))

    def forward(self, node_feat, A_norm, edge_src_idx, edge_dst_idx, edge_feat):
        H1 = self.layer1.forward(node_feat, A_norm)
        H2 = self.layer2.forward(H1, A_norm)
        src_emb = H2[edge_src_idx]
        dst_emb = H2[edge_dst_idx]
        combined = np.hstack([src_emb, dst_emb, edge_feat])
        logits = combined @ self.W_clf + self.b_clf
        probs = self._sigmoid(logits).ravel()
        return probs, combined, H1, H2

    def train_step(self, node_feat, A_norm, edge_src_idx, edge_dst_idx,
                   edge_feat, y, sample_weight=None):
        probs, combined, H1, H2 = self.forward(
            node_feat, A_norm, edge_src_idx, edge_dst_idx, edge_feat
        )
        eps = 1e-7
        # Binary cross-entropy with optional class weights
        if sample_weight is not None:
            w = sample_weight
        else:
            w = np.ones_like(y)
        loss = -np.mean(w * (y * np.log(probs + eps) + (1 - y) * np.log(1 - probs + eps)))

        # Backward through classifier
        d_logits = (probs - y) * w / len(y)
        d_logits = d_logits.reshape(-1, 1)
        d_combined = d_logits @ self.W_clf.T
        self.W_clf -= self.lr * (combined.T @ d_logits)
        self.b_clf -= self.lr * d_logits.sum(axis=0)

        # Backward through GCN layers
        d_src_emb = d_combined[:, :self.hidden_dim]
        d_dst_emb = d_combined[:, self.hidden_dim:2 * self.hidden_dim]

        d_H2 = np.zeros_like(H2)
        np.add.at(d_H2, edge_src_idx, d_src_emb)
        np.add.at(d_H2, edge_dst_idx, d_dst_emb)

        d_H1 = self.layer2.backward(d_H2, self.lr)
        self.layer1.backward(d_H1, self.lr)

        return loss

    def predict(self, node_feat, A_norm, edge_src_idx, edge_dst_idx, edge_feat):
        probs, _, _, _ = self.forward(
            node_feat, A_norm, edge_src_idx, edge_dst_idx, edge_feat
        )
        return probs

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "layer1_W": self.layer1.W, "layer1_b": self.layer1.b,
                "layer2_W": self.layer2.W, "layer2_b": self.layer2.b,
                "W_clf": self.W_clf, "b_clf": self.b_clf,
                "hidden_dim": self.hidden_dim,
                "edge_feat_dim": self.edge_feat_dim,
            }, f)
"""Run ML baseline and GNN experiments on processed AML data.

Usage: python scripts/run_baseline.py [--sample N] [--skip-gnn]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.config import ExperimentConfig, SplitConfig
from models.features import build_feature_matrix, prepare_base_features
from models.train import train_and_predict
from models.evaluate import evaluate_experiment
from models.gnn import GCN


def load_data(sample_size: int = 0):
    txns = pd.read_csv(ROOT / "data" / "processed" / "transactions.csv")
    labels = pd.read_csv(ROOT / "data" / "processed" / "labels.csv")
    txns["ts"] = pd.to_datetime(txns["ts"])
    if sample_size > 0 and sample_size < len(txns):
        # Shuffle before sampling to get rows across the full time range,
        # then re-sort by timestamp for chronological processing.
        txns = txns.sample(n=sample_size, random_state=42).sort_values("ts").reset_index(drop=True)
        labels = labels[labels["txn_id"].isin(txns["txn_id"])]
    return txns, labels


def split_data(txns, labels, cfg: SplitConfig):
    """Chronological split with data-driven or config boundaries.

    Policy: transactions with identical timestamps are kept together
    (not split across partitions) to prevent same-time information leakage.
    """
    y = labels.set_index("txn_id")["is_laundering"]
    txns = txns.copy()
    txns["label"] = txns["txn_id"].map(y).fillna(0).astype(int)

    # Compute boundaries
    train_end, val_end = cfg.compute_boundaries(txns["ts"])

    # Split
    train = txns[txns.ts <= train_end].copy()
    val   = txns[(txns.ts > train_end) & (txns.ts <= val_end)].copy()
    test  = txns[txns.ts > val_end].copy()

    # Assertions
    total_retained = len(train) + len(val) + len(test)
    assert total_retained == len(txns), (
        f"Row loss: {len(txns)} input, {total_retained} retained"
    )
    assert len(set(train.index) & set(val.index)) == 0, "train/val overlap"
    assert len(set(val.index) & set(test.index)) == 0, "val/test overlap"
    assert len(set(train.index) & set(test.index)) == 0, "train/test overlap"
    if len(val) > 0 and len(train) > 0:
        assert val["ts"].min() >= train["ts"].max(), "val timestamps not after train"
    if len(test) > 0 and len(val) > 0:
        assert test["ts"].min() >= val["ts"].max(), "test timestamps not after val"

    # Report boundary info
    boundary_info = {
        "train_end": str(train_end),
        "val_end": str(val_end),
    }
    return train, val, test, boundary_info


def build_adjacency(train_txns, account_map, n_nodes):
    """Build normalized adjacency for training graph."""
    src_idx = train_txns["src"].map(account_map).values
    dst_idx = train_txns["dst"].map(account_map).values
    data = np.ones(len(src_idx), dtype=np.float32)
    A = sparse.csr_matrix((data, (src_idx, dst_idx)), shape=(n_nodes, n_nodes))
    A = A + A.T
    A.setdiag(1)
    d = np.array(A.sum(axis=1)).ravel()
    d_inv_sqrt = 1.0 / np.sqrt(d + 1e-10)
    D_inv_sqrt = sparse.diags(d_inv_sqrt)
    return D_inv_sqrt @ A @ D_inv_sqrt


def make_edge_data(txns_subset, account_map):
    src = txns_subset["src"].map(account_map).values
    dst = txns_subset["dst"].map(account_map).values
    ts = pd.to_datetime(txns_subset["ts"])
    amt = np.log1p(txns_subset["amount"].clip(lower=0).values)
    hour = ts.dt.hour.values.astype(np.float32) / 24.0
    ext = txns_subset["ext_bank"].astype(int).values.astype(np.float32) if "ext_bank" in txns_subset.columns else np.zeros(len(txns_subset))
    edge_feat = np.column_stack([amt, hour, ext])
    y = txns_subset["label"].values.astype(np.float32)
    return src, dst, edge_feat, y


def run_gnn(train, val, test, account_map, node_feat, A_norm, cfg):
    n_nodes = len(account_map)
    tr_src, tr_dst, tr_ef, tr_y = make_edge_data(train, account_map)
    va_src, va_dst, va_ef, va_y = make_edge_data(val, account_map)
    te_src, te_dst, te_ef, te_y = make_edge_data(test, account_map)

    pos_count = max(tr_y.sum(), 1)
    neg_count = max(len(tr_y) - pos_count, 1)
    pos_weight = neg_count / pos_count
    sample_weight = np.where(tr_y == 1, pos_weight, 1.0)

    gcn = GCN(node_feat_dim=node_feat.shape[1], edge_feat_dim=3,
              hidden_dim=32, lr=0.005, epochs=30, seed=cfg.random_state)
    t0 = perf_counter()
    for _ in range(gcn.epochs):
        gcn.train_step(node_feat, A_norm, tr_src, tr_dst, tr_ef, tr_y, sample_weight)
    train_time = perf_counter() - t0

    val_proba = gcn.predict(node_feat, A_norm, va_src, va_dst, va_ef)
    test_proba = gcn.predict(node_feat, A_norm, te_src, te_dst, te_ef)
    model_path = ROOT / "artifacts" / "models" / "gnn_model.pkl"
    gcn.save(model_path)
    return {
        "status": "completed", "val_proba": val_proba, "test_proba": test_proba,
        "train_time_s": round(train_time, 2), "epochs": gcn.epochs,
        "hidden_dim": gcn.hidden_dim, "n_nodes": n_nodes,
        "n_train_edges": len(train), "model_path": str(model_path),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=0)
    parser.add_argument("--skip-gnn", action="store_true")
    args = parser.parse_args()

    cfg = ExperimentConfig(sample_size=args.sample)
    results_dir = ROOT / "artifacts" / "results"
    models_dir = ROOT / "artifacts" / "models"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    txns, labels = load_data(cfg.sample_size)
    ts_min, ts_max = txns["ts"].min(), txns["ts"].max()
    print(f"  {len(txns)} transactions, {int(labels.is_laundering.sum())} positive")
    print(f"  timestamp range: {ts_min} to {ts_max}")
    print(f"  unique timestamps: {txns['ts'].nunique()}")

    print("Splitting...")
    train, val, test, boundary_info = split_data(txns, labels, cfg.split)
    print(f"  boundaries: train_end={boundary_info['train_end']}, val_end={boundary_info['val_end']}")
    split_sizes = {
        "train": {"rows": len(train), "positive": int(train.label.sum())},
        "val":   {"rows": len(val),   "positive": int(val.label.sum())},
        "test":  {"rows": len(test),  "positive": int(test.label.sum())},
        "boundaries": boundary_info,
    }
    for k, v in split_sizes.items():
        if k == "boundaries":
            continue
        print(f"  {k}: {v['rows']} rows, {v['positive']} positive")

    print("Building features...")
    t0 = perf_counter()
    X_train, names, enc = build_feature_matrix(train, cfg.features)
    X_val, _, _ = build_feature_matrix(val, cfg.features, fit_encoder=enc)
    X_test, _, _ = build_feature_matrix(test, cfg.features, fit_encoder=enc)
    print(f"  {len(names)} features in {perf_counter()-t0:.1f}s")

    y_train, y_val, y_test = train.label.values, val.label.values, test.label.values

    print("Training baselines...")
    results = train_and_predict(
        X_train, y_train, X_val, y_val, X_test, y_test,
        names, cfg.random_state, models_dir,
    )

    print("Evaluating...")
    report = evaluate_experiment(results, y_val, y_test, split_sizes, results_dir)
    for name, m in report["models"].items():
        print(f"  {name}: val F1={m['val']['f1']:.4f}  test PR-AUC={m['test']['pr_auc']:.4f}  "
              f"test F1={m['test']['f1']:.4f}  P={m['test']['precision']:.4f}  R={m['test']['recall']:.4f}  "
              f"time={m['train_time_s']:.2f}s")

    if not args.skip_gnn:
        print("\nGNN experiment...")
        all_accts = pd.concat([txns["src"], txns["dst"]]).unique()
        acct_map = {a: i for i, a in enumerate(all_accts)}
        print(f"  {len(acct_map)} accounts")
        n_nodes = len(acct_map)
        nf = np.zeros((n_nodes, 3), dtype=np.float32)
        for _, row in train.iterrows():
            si, di = acct_map.get(row["src"]), acct_map.get(row["dst"])
            if si is not None:
                nf[si, 0] += 1
                nf[si, 1] += row["amount"]
            if di is not None:
                nf[di, 2] += 1
        for c in range(3):
            mx = nf[:, c].max()
            if mx > 0:
                nf[:, c] /= mx

        A_norm = build_adjacency(train, acct_map, n_nodes)
        gnn_res = run_gnn(train, val, test, acct_map, nf, A_norm, cfg)
        report["gnn"] = gnn_res

        if gnn_res["status"] == "completed":
            from models.evaluate import select_threshold, compute_metrics
            thr = select_threshold(y_val, gnn_res["val_proba"])
            gnn_val_m = compute_metrics(y_val, gnn_res["val_proba"], thr)
            gnn_test_m = compute_metrics(y_test, gnn_res["test_proba"], thr)
            report["gnn"]["val_metrics"] = gnn_val_m
            report["gnn"]["test_metrics"] = gnn_test_m
            print(f"  GNN: val PR-AUC={gnn_val_m['pr_auc']:.4f}  test PR-AUC={gnn_test_m['pr_auc']:.4f}")
        else:
            print(f"  GNN skipped: {gnn_res.get('reason')}")

    with open(results_dir / "full_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport: {results_dir / 'full_report.json'}")


if __name__ == "__main__":
    main()
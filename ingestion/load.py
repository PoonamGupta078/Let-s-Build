"""File I/O for IBM AML ingestion: load raw CSVs, validate, write outputs.

Raw files are never modified (tests assert this). Cleaned outputs go to
data/processed/, a reproducible sample to data/samples/.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .schema import ibm_string_dtypes, normalize_ibm_transactions
from .validate import ValidationPolicy, validate_transactions

ACCOUNT_RENAME = {
    "Bank Name": "bank_name",
    "Bank ID": "bank_id",
    "Account Number": "account_id",
    "Entity ID": "entity_id",
    "Entity Name": "entity_name",
}
ACCOUNT_COLUMNS = ["account_id", "bank_id", "bank_name", "entity_id", "entity_name"]


def load_ibm_raw(path: Path, nrows: int | None = None) -> pd.DataFrame:
    """Read HI-Small_Trans.csv. Bank/account ids are strings (leading zeros
    like '010' must survive); pandas renames the second 'Account' header to
    'Account.1' automatically."""
    return pd.read_csv(path, nrows=nrows, dtype=ibm_string_dtypes())


def load_ibm_accounts(path: Path) -> pd.DataFrame:
    """Read HI-Small_accounts.csv into normalized account metadata."""
    df = pd.read_csv(
        path,
        dtype={"Bank ID": "string", "Account Number": "string", "Entity ID": "string"},
    )
    df = df.rename(columns=ACCOUNT_RENAME)
    return df[ACCOUNT_COLUMNS]


def reproducible_sample(txns: pd.DataFrame, size: int) -> pd.DataFrame:
    """Deterministic systematic sample (every k-th row), re-sorted by time.

    Systematic sampling uses no RNG, so the same input always yields the same
    sample — no seed to manage. Size larger than the frame returns everything.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    n = len(txns)
    if n == 0 or size >= n:
        return txns.sort_values(["ts", "txn_id"], kind="mergesort").reset_index(drop=True)
    step = n / size
    idx = np.unique(np.floor(np.arange(size) * step).astype(int))
    return (
        txns.iloc[idx]
        .sort_values(["ts", "txn_id"], kind="mergesort")
        .reset_index(drop=True)
    )


def process_ibm_dataset(
    trans_path: Path,
    accounts_path: Path | None,
    out_dir: Path,
    sample_size: int = 5000,
    sample_dir: Path | None = None,
    policy: ValidationPolicy | None = None,
) -> dict:
    """Full pipeline: raw IBM CSVs -> validated internal-schema outputs.

    Writes transactions.csv, labels.csv, accounts.csv and data_quality.json to
    out_dir, and sample_transactions.csv to sample_dir (default: sibling
    'samples' directory). Returns the summary written to data_quality.json.
    """
    trans_path = Path(trans_path)
    out_dir = Path(out_dir)
    sample_dir = Path(sample_dir) if sample_dir else out_dir.parent / "samples"
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    raw = load_ibm_raw(trans_path)
    txns, labels = normalize_ibm_transactions(raw)
    report = validate_transactions(txns, policy)

    accepted = (
        report.accepted.sort_values(["ts", "txn_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    accepted.to_csv(out_dir / "transactions.csv", index=False)

    labels_df = pd.DataFrame(
        {
            "txn_id": accepted["txn_id"].to_numpy(),
            "is_laundering": labels.reindex(accepted["txn_id"]).to_numpy(),
        }
    )
    labels_df.to_csv(out_dir / "labels.csv", index=False)

    if accounts_path is not None and Path(accounts_path).exists():
        load_ibm_accounts(Path(accounts_path)).to_csv(
            out_dir / "accounts.csv", index=False
        )

    sample = reproducible_sample(accepted, sample_size)
    sample.to_csv(sample_dir / "sample_transactions.csv", index=False)

    summary = {
        "source_file": trans_path.name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": report.counts,
        "policy": asdict(policy or ValidationPolicy()),
        "columns": list(accepted.columns),
        "sample_rows": int(len(sample)),
    }
    if len(accepted):
        summary["timestamp_min"] = str(accepted["ts"].min())
        summary["timestamp_max"] = str(accepted["ts"].max())
    (out_dir / "data_quality.json").write_text(json.dumps(summary, indent=2))
    return summary
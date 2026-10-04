"""Build processed dataset and reproducible sample from the raw IBM AML CSVs.

Usage (Windows PowerShell, from the repo root, venv active):
    python scripts/build_dataset.py
    python scripts/build_dataset.py --sample 5000 --keep-self-transfers

Defaults: data/HI-Small_Trans.csv + data/HI-Small_accounts.csv ->
          data/processed/ + data/samples/. Raw files are never modified.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # allow `python scripts/build_dataset.py` from anywhere
    sys.path.insert(0, str(ROOT))

from ingestion.load import process_ibm_dataset
from ingestion.validate import ValidationPolicy


def main() -> None:
    """Parse CLI args and run the ingestion pipeline once."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trans", type=Path, default=ROOT / "data" / "HI-Small_Trans.csv")
    parser.add_argument("--accounts", type=Path, default=ROOT / "data" / "HI-Small_accounts.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--samples", type=Path, default=ROOT / "data" / "samples")
    parser.add_argument("--sample-size", type=int, default=5000)
    parser.add_argument(
        "--keep-self-transfers",
        action="store_true",
        help="keep IBM 'Reinvestment' self-transfers instead of rejecting them",
    )
    args = parser.parse_args()

    policy = ValidationPolicy(reject_self_transfers=not args.keep_self_transfers)
    summary = process_ibm_dataset(
        args.trans,
        args.accounts,
        args.out,
        sample_size=args.sample_size,
        sample_dir=args.samples,
        policy=policy,
    )
    counts = summary["counts"]
    print(f"source        : {summary['source_file']}")
    print(f"total rows    : {counts['total']:,}")
    print(f"accepted      : {counts['accepted']:,}")
    print(f"rejected      : {counts['rejected']:,}")
    for rule in ("missing_id", "bad_timestamp", "bad_amount", "negative_amount",
                 "self_transfer", "duplicate_txn_id"):
        print(f"  {rule:<18}: {counts[rule]:,}")
    print(f"sample rows   : {summary['sample_rows']:,}")
    print(f"outputs       : {args.out}")


if __name__ == "__main__":
    main()
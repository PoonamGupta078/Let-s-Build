"""Inspect raw IBM AML CSVs: columns, dtypes, sample rows and basic data-quality stats.

Usage:  python scripts/inspect_data.py [file1.csv file2.csv ...]
Defaults to data/HI-Small_Trans.csv and data/HI-Small_accounts.csv.
Prints a report to stdout; never modifies the raw files.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = [
    ROOT / "data" / "HI-Small_Trans.csv",
    ROOT / "data" / "HI-Small_accounts.csv",
]


def inspect_csv(path: Path) -> None:
    """Print schema and quality summary for one CSV file."""
    print(f"\n{'=' * 70}\nFILE: {path}")
    if not path.exists():
        print("  !! FILE NOT FOUND")
        return
    size_mb = path.stat().st_size / 1e6
    print(f"size: {size_mb:.1f} MB")

    # First pass: cheap peek at the header and a few rows only.
    peek = pd.read_csv(path, nrows=5)
    print(f"\ncolumns ({len(peek.columns)}):")
    for col in peek.columns:
        print(f"  - {col!r}  (peek dtype: {peek[col].dtype})")
    print("\nfirst 3 rows:")
    print(peek.head(3).to_string())

    # Second pass: full read for real dtypes, nulls and duplicate counts.
    df = pd.read_csv(path)
    print(f"\nrows: {len(df):,}")
    print("dtypes after full parse:")
    print(df.dtypes.to_string())
    nulls = df.isna().sum()
    print("null counts per column:")
    print(nulls.to_string())

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            s = df[col]
            print(
                f"numeric stats '{col}': min={s.min()!r} max={s.max()!r} "
                f"n_unique={s.nunique():,}"
            )


def main(argv: list[str]) -> None:
    """Inspect the given CSV paths, or the default IBM AML files."""
    paths = [Path(a) for a in argv[1:]] or DEFAULT_FILES
    print(f"pandas {pd.__version__}")
    for p in paths:
        inspect_csv(p)


if __name__ == "__main__":
    main(sys.argv)
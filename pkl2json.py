#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that scans the current directory for all `.pkl` files, loads each one with pickle, and validates that its contents are a pandas DataFrame, printing a warning and skipping any file that isn't or that fails to load.
It should report each loaded file's shape, then concatenate all valid DataFrames into a single merged DataFrame, remove duplicate rows, and print progress messages including counts of files found, rows merged, and duplicates dropped.
Handle the case where no `.pkl` files exist or none contain valid DataFrames by printing an appropriate message and exiting gracefully."""

import glob
import json
import os
import pickle
from pathlib import Path
import pandas as pd


def load_pkl_file(filepath):
    try:
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        if not isinstance(data, pd.DataFrame):
            print(
                f"Warning: {filepath} does not contain a DataFrame (got {type(data)}). Skipping."
            )
            return None
        print(f"Loaded {filepath}: {len(data)} rows, {len(data.columns)} columns")
        return data
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def main():
    pkl_files = sorted(glob.glob("*.pkl"))
    if not pkl_files:
        print("No .pkl files found in current directory.")
        return
    print(f"Found {len(pkl_files)} pickle file(s):\n")
    for f in pkl_files:
        print(f"  - {f}")
    print()
    dataframes = []
    for filepath in pkl_files:
        df = load_pkl_file(filepath)
        if df is not None:
            dataframes.append(df)
    if not dataframes:
        print("No valid DataFrames loaded. Exiting.")
        return
    print(f"\nMerging {len(dataframes)} DataFrames...")
    merged_df = pd.concat(dataframes, ignore_index=True)
    print(f"Merged shape: {merged_df.shape}")
    # Deduplicate
    initial_count = len(merged_df)
    merged_df = merged_df.drop_duplicates()
    final_count = len(merged_df)
    print(f"Dropped {initial_count - final_count} duplicate rows")
    print(f"Final shape: {merged_df.shape}")
    records = json.loads(merged_df.to_json(orient="records", date_format="iso"))
    output_file = "merged_deduped.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"\n✓ Wrote {len(records)} records to {output_file}")


if __name__ == "__main__":
    main()

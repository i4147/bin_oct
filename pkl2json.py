#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory for all pickle files (with a .pkl extension), loads each one, and validates that it contains a tabular dataset. The script should discover the files in a consistent, s the user which files were found before processing them. For each file, it should attempt to deserialize the contents and confirm the result is a structured table; if a file holds some other kind of object, it should print a clear warning naming the file and the actual type encountered, then skip it. If loading fails for any reason ( file, unreadable data, etc.), it should print an error message identifying the file and theing the remaining files rather than crashing. For every successfully loaded table, it should report the number of rows and columns. The script should collect all valid tables and then combine them into a single consolidated table for further use, handling the case where no valid files exist or noables could be loaded by informing the user and exiting gracefully. The script should be runnable as a standalone command-line tool with arguments, and its output should be clear, concy to follow.
---"""

from __future__ import annotations
import glob
import json
import pickle
import pandas as pd


def load_pkl_file(filepath):
    try:
        with open(filepath, "rb") as f:
            data = pickle.load(f)
        if not isinstance(data, pd.DataFrame):
            print(f"Warning: {filepath} does not contain a DataFrame (got {type(data)}). Skipping.")
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

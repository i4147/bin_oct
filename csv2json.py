#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that converts a CSV file into a JSON key-value map.
It should take a single CSV file path as a command-line argument, read the first two columns of each row (using the first row as a header, skipped from data processing), and build a dictionary mapping trimmed values from the first column to trimmed values from the second column, skipping rows with empty keys or fewer than two columns.
The script should validate that the input file exists and that the CSV has at least two columns, printing an error message and exiting with status 1 otherwise.
Finally, it should write the resulting dictionary as indented, UTF-8-encoded JSON to a file with the same name as the input but with a .json extension, and print a confirmation message showing the source and destination file paths."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def csv_to_json_map(csv_file: str) -> None:
    csv_path = Path(csv_file)
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}")
        sys.exit(1)
    json_path = csv_path.with_suffix(".json")
    result = {}
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or len(header) < 2:
            print("Error: CSV must have at least two columns")
            sys.exit(1)
        for row in reader:
            if len(row) < 2:
                continue
            key = row[0].strip()
            value = row[1].strip()
            if key:
                result[key] = value
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"Converted : {csv_path} → {json_path}")


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <file.csv>")
        sys.exit(1)
    csv_to_json_map(sys.argv[1])


if __name__ == "__main__":
    raise SystemExit(main())

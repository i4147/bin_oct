#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a two-column CSV file into a JSON object mapping keys to values. The script should accept a single command-line argument giving the path to the CSV file and print a usage message if the argument is missing or extra arguments are supplied.
Behavior requirements:
- Verify that the input file exists; if it does not, report a clear error message and exit with a non-zero status.
- Read the CSV as UTF-8 text, treating the first row as a header that is skipped. The header must contain at least two columns; otherwise report an error and exit with a non-zero status.
- For each subsequent row, use the first column as the key and the second column as the value, trimming surrounding whitespace from both. Skip rows that have fewer than two columns and skip rows whose key is empty.
- Later rows with a duplicate key should overwrite earlier values.
- Write the resulting mapping to a JSON file placed next to the input CSV, sharing the same base name with a .json extension. The JSON should be human-readable with indentation and must preserve non-ASCII characters without escaping them.
- Upon success, print a short confirmation message showing the source and destination paths.
The script should be a standalone command-line tool with a clear entry point, robust error handling for invalid input, and no interactive prompts.
---"""

from __future__ import annotations
import csv
import json
from pathlib import Path
import sys


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

#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that converts a CSV file into a JSON file.
The script should take the input CSV file path as a command-line argument, read it using csv.DictReader to preserve column headers as keys, and write the resulting list of records to a JSON file with the same base name but a .json extension, using indented, UTF-8 friendly formatting.
If no input file argument is provided, it should print a usage message and exit with a non-zero status code."""

from __future__ import annotations
import csv
import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python csv_to_json.py <input.csv>")
        sys.exit(1)
    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".json")
    with open(input_path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        data = list(reader)
    with open(output_path, mode="w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    raise SystemExit(main())

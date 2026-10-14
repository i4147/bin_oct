#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a CSV file into a JSON file. The script should accept the path to an input CSV file as a command-line argument and produce a JSON file saved alongside it, using the same base name with a .json extension. Each row of the CSV, with its first line serving as the column headers, should become one record in the output, and the output should be a JSON array of these records. The script should read and write using UTF-8 encoding, preserve non-ASCII characters as-is in the output rather than escaping them, and format the JSON with readable indentation. If the user runs the script without providing an input file argument, it should print a brief usage message to the console and exit with a non-zero status code. Ensure the script can be run directly from the command line and exits cleanly after completing the conversion.
---"""

from __future__ import annotations
import csv
import json
from pathlib import Path
import sys


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

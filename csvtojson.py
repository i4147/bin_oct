#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that converts a CSV file into a JSON file. The script should accept the path to an input CSV file as a command-line argument, read its contents using the first row as column headers, and transform each subsequent row into a record keyed by those headers. All records should be collected into a single list and saved to a new JSON file placed alongside the original, using the same base name with a .json extension. The output should be human-readable with indentation and must preserve UTF-8 character encoding. The script should run as a standalone command-line tool and handle the input path cleanly so that it can be invoked directly from a terminal.
---"""

from __future__ import annotations
import csv
import json
from pathlib import Path
import sys


def convert_csv_to_json(input_path: Path) -> None:
    output_path = input_path.with_suffix(".json")
    with input_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        data = list(reader)
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    input_path = Path(sys.argv[1])
    convert_csv_to_json(input_path)

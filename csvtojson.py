#!/data/data/com.termux/files/usr/bin/python
import csv
import json
import sys
from pathlib import Path


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

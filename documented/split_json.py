#!/data/data/com.termux/files/usr/bin/env python
"""split_json.py -- split a JSON file into several files."""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        raise SystemExit(f"Usage: python {Path(sys.argv[0]).name} input.json")

    input_path = Path(sys.argv[1])

    with input_path.open("r", encoding="utf-8") as f:
        records = json.load(f)

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            print(f"Skipping record {index}: expected a JSON object")
            continue

        for name, content in record.items():
            # Use only the name, preventing output outside the current folder.
            output_name = Path(name).name
            output_path = Path(output_name).with_suffix(".txt")

            # Avoid overwriting if different input names map to the same .txt name.
            if output_path.exists():
                output_path = output_path.with_name(f"{output_path.stem}_{index}{output_path.suffix}")

            output_path.write_text(str(content), encoding="utf-8")
            print(f"Saved {output_path}")


if __name__ == "__main__":
    main()

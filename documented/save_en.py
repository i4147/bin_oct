#!/data/data/com.termux/files/usr/bin/env python
"""save_en.py -- write the text of an input file to a ``.txt`` file."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    """Copy the text of the input file to a plain ``.txt`` file."""
    input_path = Path(sys.argv[1])
    output_path = input_path.with_suffix(".txt")
    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)
    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(record["en"] + "\n")
    print(f"Saved English text to {output_path}")


if __name__ == "__main__":
    main()

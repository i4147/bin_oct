#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that takes a JSON file path as its first argument, reads the file as a list of records, and extracts the "en" field from each record.
It should write these English strings, one per line, into a new text file that shares the same base name as the input but with a ".txt" extension.
After writing, the script should print a confirmation message indicating where the output was saved."""

import json
import sys
from pathlib import Path


def main() -> None:
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

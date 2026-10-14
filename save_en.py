#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a Jline argument,ads the file'sexpected to be a list of records, where each record contains an English text entry), and extracts only the English text from every record. It should save these English lines, one per line, into a plain text file that uses the same base name and location as the input file but with a .txt extension, using UTF-8 encoding. After saving, it should print a short confirmation message that includes the path of the created output file.
---"""

from __future__ import annotations
import json
from pathlib import Path
import sys


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

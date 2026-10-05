#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that reformats a text file by splitting its content on a user-specified delimiter string.
It should accept two command-line arguments, a filename and a delimiter, reading the file's full text, splitting it into parts using the delimiter, stripping whitespace from each part, and rewriting the same file so each part is followed by the delimiter and a newline.
The script must validate that exactly two arguments are provided and that the delimiter is non-empty, printing a usage or error message and exiting with status 1 otherwise, and it should print a confirmation message naming the updated file upon success."""

from __future__ import annotations
import sys
from pathlib import Path


def split_file_by_delimiter(fname: str, delimiter: str) -> None:
    content = Path(fname).read_text(encoding="utf-8")
    parts = content.split(delimiter)
    with Path(fname).open("w", encoding="utf-8") as f:
        f.writelines(part.strip() + f"{delimiter}\n" for part in parts)


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python script.py <filename> <delimiter>")
        sys.exit(1)
    fname = sys.argv[1]
    delimiter = sys.argv[2]
    if not delimiter:
        print("Error: delimiter cannot be empty")
        sys.exit(1)
    split_file_by_delimiter(fname, delimiter)
    print(f"{sys.argv[1]} updated.")


if __name__ == "__main__":
    raise SystemExit(main())

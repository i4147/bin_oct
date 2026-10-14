#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that operates as a command-line tool for normalizing the segments of a text file separated by a user-specified delimiter. The tool takes exactly two arguments: the path to a UTF-8 encoded text file and the delimiter string to split on. It reads the entire file, splits its contents at every occurrence of the delimiter, trims surrounding whitespace from each resulting segment, and rewrites the file so that every segment is followed by the delimiter and a newline, with the original file replaced in place. If the argument count is wrong, the tool should print a short usage message showing the expected form and exit with a non-zero status. If the delimiter is an empty string, it should print a clear error message and exit with a non-zero status without modifying the file. On success, it should print a brief confirmation that includes the filename and then exit cleanly. The tool should be self-contained, handle the file as UTF-8 text, and avoid any other side effects or output beyond the described messages.
---"""

from __future__ import annotations
from pathlib import Path
import sys


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

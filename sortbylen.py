#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for sorting the lines of a text file by their length, in place. The tool should accept a file path as a required argument and an optional flag that reverses the sort order, so that the longest lines come first instead of the shortest. If the path is missing, it should print a short usage message explaining the expected command format and exit with a non-zero status. When the file is processed, its lines should be reordered by length while preserving each line's original content and line endings, and the file should be overwritten with the sorted result using UTF-8 encoding. After saving, the tool should print a brief confirmation that includes the file name and whether reverse ordering was applied. Handle the input as line-based text, keep the script self-contained and easy to run from the terminal, and assume the target file exists and is readable.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from dh import read_lines


def sort_by_length(lines: list[str], reverse: bool = False) -> list[str]:
    return sorted(lines, key=len, reverse=reverse)


if __name__ == "__main__":
    args = sys.argv[1:]
    reverse = False
    if "-r" in args:
        reverse = True
        args.remove("-r")
    if not args:
        print("Usage: python script.py [-r] <path>")
        sys.exit(1)
    path = Path(args[0].strip())
    lines = read_lines(path, ke=True)
    sorted_lines = sort_by_length(lines, reverse=reverse)
    path.write_text("".join(sorted_lines), encoding="utf8")
    print(f"{path.name} updated (reverse={reverse})")

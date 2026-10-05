#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that takes a file path and a target character as arguments, reads the file line by line using a helper function `read_lines` from a local module `dh`, and processes each non-empty stripped line: if the target character is found in the line, it truncates the line to start from that character's first occurrence; otherwise it keeps the stripped line as-is.
All processed lines are collected into a list, and if the list is non-empty, the original file is overwritten with the joined lines (newline-separated, UTF-8 encoding).
The script also defines an unused constant THRESHOLD set to 1048576 (1MB)."""

from __future__ import annotations
import sys
from pathlib import Path
from dh import read_lines

THRESHOLD = 1048576
if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[indx:]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")

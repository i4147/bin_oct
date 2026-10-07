#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that takes a file path and a target character as arguments (sys.argv[1] and sys.argv[2]).
It should read the file's lines, and for each non-empty line, if the target character is found, truncate the line at that character's first occurrence; otherwise keep the stripped line as is.
Empty lines should be discarded.
Finally, the script should overwrite the original file with the processed lines joined by newlines, using UTF-8 encoding, only if there is at least one resulting line."""

from __future__ import annotations
import sys
from pathlib import Path


def read_lines(path):
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[:indx]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")

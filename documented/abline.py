#!/data/data/com.termux/files/usr/bin/env python

"""abline.py -- split each line at a character and keep one side of it.

Mode ``-a`` keeps the text *before* the first occurrence of the target
character, mode ``-b`` keeps the text *after* it.  Lines without the character
are kept unchanged, blank lines are dropped, and the kept fragments are
rejoined with newlines and written back to the same file, which makes the
filter destructive by design.

Usage: ``abline.py {-a|-b} FILE CHAR``
"""

from __future__ import annotations

import sys
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    """Return the lines of *path* with their line endings kept."""
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def process_a(line: str, target_char: str) -> str:
    """Return the part of *line* before the first *target_char*."""
    stripped = line.strip()
    if stripped and target_char in stripped:
        indx = stripped.index(target_char)
        return stripped[:indx]
    elif stripped:
        return stripped
    return ""


def process_b(line: str, target_char: str) -> str:
    """Return the part of *line* after the first *target_char*."""
    stripped = line.strip()
    if stripped and target_char in stripped:
        indx = stripped.index(target_char)
        return stripped[indx + 1 :]
    elif stripped:
        return stripped
    return ""


if __name__ == "__main__":
    mode = sys.argv[1]
    file_name = Path(sys.argv[2])
    target_char = sys.argv[3]
    nl: list[str] = []
    for line in read_lines(file_name):
        if mode == "-a":
            result = process_a(line, target_char)
        else:
            result = process_b(line, target_char)
        if result:
            nl.append(result)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")

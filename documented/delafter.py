#!/data/data/com.termux/files/usr/bin/env python
"""delafter.py -- cut each line after a delimiter.

Everything from the first occurrence of the character onwards is removed, lines without
it are kept and the file is rewritten in place.
"""

from __future__ import annotations

import sys
from pathlib import Path


def read_lines(path):
    """Return the lines of *path* with their line endings preserved."""
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

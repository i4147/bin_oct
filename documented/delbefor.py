#!/data/data/com.termux/files/usr/bin/env python
"""delbefor.py -- cut each line before a delimiter.

Everything up to and including the first occurrence of the character is removed and the
file is rewritten in place.
"""

from __future__ import annotations

import sys
from pathlib import Path


def read_lines(path):
    """Return the lines of *path* with their line endings preserved."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            yield line


if __name__ == "__main__":
    file_name = Path(sys.argv[1])
    nl = []
    target_char = sys.argv[2]
    for line in read_lines(file_name):
        stripped = line.strip()
        if stripped and target_char in stripped:
            indx = stripped.index(target_char)
            cleaned = stripped[indx + 1 :]
            nl.append(cleaned)
        elif stripped:
            nl.append(stripped)
    if nl:
        file_name.write_text("\n".join(nl), encoding="utf-8")

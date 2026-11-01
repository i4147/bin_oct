#!/data/data/com.termux/files/usr/bin/env python
"""faprinter.py -- print a text file one line at a time.

The ``ylines`` helper yields lines lazily so large files are never read twice.
"""

from __future__ import annotations

import sys
from pathlib import Path

from faprint import faprint as pp


def ylines(path: Path):
    """Yield the lines of *path*, keeping their line endings."""
    with path.open(encoding="utf-8") as f:
        yield from f


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    for k in ylines(fn):
        print(pp(k))

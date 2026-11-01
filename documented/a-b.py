#!/data/data/com.termux/files/usr/bin/env python

"""a-b.py -- remove every line of one file from another, in place.

The lines of the second file act as a delete list for the first file
(``a - b``).  Line endings are ignored while comparing, and the filtered
result replaces the first file through a temporary sibling file followed by
an atomic ``replace``, so an interrupted run cannot truncate the original.

Usage: ``a-b.py FILE_A FILE_B``
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """Rewrite ``argv[1]`` without the lines that also appear in ``argv[2]``."""
    file_a = Path(sys.argv[1])
    file_b = Path(sys.argv[2])
    b_lines = {line.rstrip("\n") for line in file_b.read_text(encoding="utf-8").splitlines()}
    a_lines = file_a.read_text(encoding="utf-8").splitlines(keepends=True)
    kept_lines = [line for line in a_lines if line.rstrip("\n") not in b_lines]
    tmp_path = file_a.with_suffix(file_a.suffix + ".tmp")
    tmp_path.write_text("".join(kept_lines), encoding="utf-8")
    tmp_path.replace(file_a)


if __name__ == "__main__":
    raise SystemExit(main())

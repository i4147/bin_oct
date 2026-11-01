#!/data/data/com.termux/files/usr/bin/env python
"""joinlines.py -- join all lines of a file into a single string."""

from __future__ import annotations

from pathlib import Path
from sys import argv


def main() -> None:
    """Join the lines of a file into one string and write it back."""
    nl = ""
    with Path(argv[1]).open(encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                nl += line.strip("\n")
    Path(argv[1]).write_text(nl + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

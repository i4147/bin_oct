#!/data/data/com.termux/files/usr/bin/python

from __future__ import annotations
from pathlib import Path
import pydoc
import sys


def main() -> None:
    pydoc.pager(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())

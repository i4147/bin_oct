#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a simple command-line text file viewer. It should accept a single file path as its command-line argument, read the file's contents as text (tolerating any invalid byte sequences without crashing), and display the full contents in an interactive, scrollable pager so the user can page through long files comfortably. The script should exit cleanly once the user dismisses the viewer, and it should handle a missing or unreadable file path gracefully with a clear error message and a non-zero exit status. Keep the program minimal, dependency-free, and suitable for use in a standard terminal environment.
---"""

from __future__ import annotations
from pathlib import Path
import pydoc
import sys


def main() -> None:
    pydoc.pager(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())

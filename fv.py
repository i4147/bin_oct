#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that takes a single file path as its first argument, reads the file's entire contents as UTF-8 text (replacing any invalid byte sequences instead of raising errors), and displays the text using Python's built-in pydoc pager for convenient scrollable viewing in the terminal.
The script should expose a main() function guarded by the standard "if __name__ == '__main__'" idiom and call it via SystemExit so the process exit code reflects main()'s return value.
Use pathlib.Path to handle the file reading and sys.argv to access the command-line argument.
"""

from __future__ import annotations
import pydoc
import sys
from pathlib import Path


def main() -> None:
    pydoc.pager(Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace"))


if __name__ == "__main__":
    raise SystemExit(main())

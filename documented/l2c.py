#!/data/data/com.termux/files/usr/bin/env python
"""l2c.py -- copy a line of a file to the clipboard.

The line is read by index and handed to ``termux-clipboard-set``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def copy_line_to_clipboard(filename: str, indx) -> None:
    """Copy line *indx* of *filename* to the clipboard."""
    input_file = Path(filename)
    with input_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    content_to_copy = lines[indx].strip()
    process = subprocess.Popen(
        ["termux-clipboard-set"],
        stdin=subprocess.PIPE,
        text=True,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    """Copy the requested line of a file to the clipboard, defaulting to the last
    one."""
    fn = sys.argv[1].strip()
    lindex = int(sys.argv[2].strip())
    copy_line_to_clipboard(fn, lindex)


if __name__ == "__main__":
    raise SystemExit(main())

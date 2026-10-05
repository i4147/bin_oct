#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script for Termux (Android) that copies a specific line from a text file to the system clipboard.
It should accept two command-line arguments: a filename and a zero-based line index, read the file's lines, strip whitespace from the selected line, and pass that content to the "termux-clipboard-set" utility via a subprocess call using stdin.
The script should expose a main() function invoked through the standard "if __name__ == '__main__'" entry point, and be structured so it can be run directly from the terminal with the filename and index as arguments."""

from __future__ import annotations
import subprocess
import sys
from pathlib import Path


def copy_line_to_clipboard(filename: str, indx) -> None:
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
    fn = sys.argv[1].strip()
    lindex = int(sys.argv[2].strip())
    copy_line_to_clipboard(fn, lindex)


if __name__ == "__main__":
    raise SystemExit(main())

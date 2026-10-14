#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that runs from the command line and copies a single line of text from a specified file to the Android/Termux clipboard. The script takes two arguments: the path to a text file and the zero-based index of the line to copy. It should read the file using UTF-8 encoding, retrieve the requested line with surrounding whitespace removed, and pass that text to the Termux clipboard utility so it becomes available for pasting. Handle the case where the file does not exist, the line index is out of range or not a valid integer, or the clipboard utility is unavailable, and report each problem with a clear message to the user and a non-zero exit status. On success, the script should exit cleanly without printing unnecessary output.
---"""

from __future__ import annotations
from pathlib import Path
import subprocess
import sys


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

#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python script that takes a file path as a command-line argument and reformats the text file by inserting extra blank lines after every existing line.
It should read the file's full content, split it into individual lines, append four newline characters to the end of each line, then rejoin all lines with a single newline separator before overwriting the original file with the modified content.
The script should accept the target file path as the first command-line argument and perform this transformation in place with no console output."""

from __future__ import annotations
from pathlib import Path
import sys


def process_file(path: Path) -> None:
    path = Path(path)
    con = path.read_text()
    nl = [(line + "\n\n\n\n") for line in con.splitlines()]
    newconn = "\n".join(nl)
    path.write_text(newconn)


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    process_file(fn)

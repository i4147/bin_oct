#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single text file path as a command-line argument and rewrites that file in place so that every existing line is followed by a large block of blank lines (three extra empty lines beyond the normal line break), effectively spacing out the content vertically. The script should read the file's full text, preserve the original line contents, insert the extra blank space after each line, and save the result back to the same file. It should run as a standalone command-line tool, expecting exactly one file argument, and handle the file reading and writing cleanly without requiring any additional user input or output beyond the modified file.
---"""

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

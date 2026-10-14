#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that reads a text file specified as a command-line argument, processes it one line at a time, and prints a formatted, pretty-printed representation of each line to the console. The script should accept the file path as its first argument, read the file using UTF-8 encoding, and avoid loading the entire file into memory at once. For each line, it should apply a formatting or pretty-printing function from an external helper module (named faprint) and output the result. The output should appear in the same order as the lines in the file, with one formatted result printed per line. The script should be a simple, self-contained command-line tool that runs when executed directly.
---"""

from __future__ import annotations
from pathlib import Path
import sys
from faprint import faprint as pp


def ylines(path: Path):
    with path.open(encoding="utf-8") as f:
        yield from f


if __name__ == "__main__":
    fn = Path(sys.argv[1])
    for k in ylines(fn):
        print(pp(k))

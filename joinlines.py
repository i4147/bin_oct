#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single file path from the command line, reads the file as UTF-8 text, removes all blank or whitespace-only lines, and joins the remaining lines together into one continuous string with no separators, then overwrites the original file with that joined text followed by a single trailing newline. The script should be runnable from the terminal with the file path as its only argument, use UTF-8 encoding for both reading and writing, and exit cleanly upon completion.
---"""

from __future__ import annotations
from pathlib import Path
from sys import argv


def main() -> None:
    nl = ""
    with Path(argv[1]).open(encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                nl += line.strip("\n")
    Path(argv[1]).write_text(nl + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

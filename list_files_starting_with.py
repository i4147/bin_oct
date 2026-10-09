#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that lists files and directories in the current working directory whose names start with a given prefix.
The prefix should be supplied as a single command-line argument; if it is missing or empty, print a usage message to stderr and exit with status code 1.
The script should iterate over entries in the current directory, skip any that are symbolic links, and print the names of the remaining entries whose names start with the specified prefix, one per line.
"""

from __future__ import annotations
import sys
from pathlib import Path


def main() -> None:
    prefix = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not prefix:
        print("Usage: python script.py <prefix>", file=sys.stderr)
        sys.exit(1)
    for entry in Path.cwd().iterdir():
        if entry.name.startswith(prefix) and not entry.is_symlink():
            print(entry.name)


if __name__ == "__main__":
    raise SystemExit(main())

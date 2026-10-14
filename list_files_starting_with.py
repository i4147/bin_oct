#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a single text prefix as a command-line argument and lists the names of all entries in the current working directory whose names begin with that prefix. The script should ignore symbolic links, so that only regular files and real directories are reported. Leading and trailing whitespace in the supplied prefix should be ignored. If no prefix is provided, or the prefix is empty after trimming whitespace, the script should print a short usage message to the error output stream that shows the expected invocation format, and exit with a non-zero status code. On success, each matching name should be printed on its own line to standard output, and the script should exit cleanly with a zero status code. The script should be a self-contained, runnable command-line tool that follows standard Python conventions, including a guard so it runs only when executed directly.
---"""

from __future__ import annotations
from pathlib import Path
import sys


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

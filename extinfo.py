#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that accepts a file extension as its single argument and recursively scans the current working directory for all files matching that extension.
It should print usage instructions and exit if no argument is given, and print a message and exit cleanly if no matching files are found.
Otherwise, it should sum up the sizes of all matched files and print both the total file count and the total size, formatting the size using a human-readable helper function called fsz imported from a local module named dh."""

import sys
from pathlib import Path
from dh import fsz


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: script.py <extension>")
        print("Example: script.py py")
        sys.exit(1)
    ext = sys.argv[1].lstrip(".")
    cwd = Path.cwd()
    files = list(cwd.rglob(f"*.{ext}"))
    if not files:
        print(f"No .{ext} files found in current directory")
        sys.exit(0)
    total_size = sum(f.stat().st_size for f in files)
    count = len(files)
    print(f"Total number of .{ext} files: {count}")
    print(f"Total size of .{ext} files: {fsz(total_size)}")


if __name__ == "__main__":
    raise SystemExit(main())

#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes a file extension from the command line and reports summary statistics for all files with that extension found recursively within the current working directory. The script should accept the extension with or without a leading dot, and should print a short usage message with an example and exit with an error status if no extension is provided. If no matching files exist, it should inform the user and exit cleanly. Otherwise, it should display the total number of matching files and their combined size in a human-readable format (such as bytes, KB, MB, or GB, as appropriate). Use the tool's standard output for all results and ensure the script runs as a standalone command-line program.
---"""

from __future__ import annotations
from pathlib import Path
import sys
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

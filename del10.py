#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that accepts a filename as a required argument and an optional minimum line length (default 10) as a second argument.
The script should read all lines from the specified file, filter out any lines whose stripped length is shorter than the given threshold, and overwrite the original file with only the remaining lines.
It must print a usage message and exit if no filename is provided, and gracefully handle a missing file with a clear error message as well as catch and report any other exceptions that occur during processing."""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    fname = sys.argv[1]
    llen = int(str(sys.argv[2]).strip()) if len(sys.argv) == 3 else 10
    lines = []
    try:
        with Path(fname).open(encoding="utf-8") as f:
            lines = f.readlines()
        filtered = [line for line in lines if len(line.strip()) >= llen]
        with Path(fname).open("w", encoding="utf-8") as f:
            f.writelines(filtered)
    except FileNotFoundError:
        print(f"Error: File '{fname}' not found.")
    except Exception as e:
        print("An error occurred:", e)

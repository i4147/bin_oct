#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that takes exactly two arguments, a filename and a prefix string, and prepends the prefix followed by a space to the beginning of every non-blank line in that file, leaving blank lines unchanged.
The script should validate that exactly two arguments are provided and that the given file exists, printing a usage or error message to stderr and exiting with status 1 otherwise.
It should read the file's lines preserving line endings, modify them in place by rewriting the file with the added prefix, and finally print a confirmation message indicating the file was updated."""

from __future__ import annotations
import sys
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <filename> <prefix_string>", file=sys.stderr)
        sys.exit(1)
    fn = Path(sys.argv[1])
    str_to_add = sys.argv[2]
    if not fn.is_file():
        print(f"Error: {fn} does not exist or is not a file", file=sys.stderr)
        sys.exit(1)
    lines = fn.read_text().splitlines(keepends=True)
    newlines = [f"{str_to_add} {line}" if line.strip() else line for line in lines]
    fn.write_text("".join(newlines))
    print(f"{fn} updated")

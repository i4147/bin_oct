#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that takes exactly two command-line arguments: the path to a text file and a prefix string. It should verify that the provided path refers to an existing regular file, and if the arguments are missing or incorrect, print a brief usage message to the error output and exit with a non-zero status. When valid, the script should prepend the given prefix, followed by a single space, to every non-blank line of the file while leaving empty or whitespace-only lines unchanged, preserving the original line endings. The modified content should be written back to the same file in place. On success, print a short confirmation message naming the updated file to standard output.
---"""

from __future__ import annotations
from pathlib import Path
import sys

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

#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that deletes a range of lines from a text file.
It should accept a filename as the first argument, a starting line number as the second argument, and an optional ending line number as the third argument; if the ending line number is omitted, deletion should continue through the last line of the file.
The script reads the file, removes the specified 1-indexed inclusive line range, writes the remaining lines back to the same file, and prints a message showing how many lines remain."""

from __future__ import annotations
import sys
from pathlib import Path


def delete_lines_from_file() -> None:
    filename = sys.argv[1]
    path = Path(filename)
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(sys.argv) == 4:
        fromline = int(sys.argv[2])
        toline = int(sys.argv[3])
    if len(sys.argv) == 3:
        fromline = int(sys.argv[2])
        toline = len(lines)
    new_lines = lines[: fromline - 1] + lines[toline:]
    path.write_text("\n".join(new_lines), encoding="utf-8")
    print(f"remained: {len(new_lines)} lines")


if __name__ == "__main__":
    delete_lines_from_file()

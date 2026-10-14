#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that runs from the command line and deletes a range of lines from a text file. The script takes a file path as its first argument, followed by either one or two line numbers: a start line and an optional end line. When only a start line is given, all lines from that point to the end of the file should be removed. When both a start and end line are given, the lines in that inclusive range (1-based numbering) should be removed. The file should be read as UTF-8 text, the remaining lines saved back to the same file, and a message reporting how many lines remain should be printed to the console. Handle the case where the arguments are missing or malformed with a clear usage message, and make sure line numbers outside the file's bounds are handled gracefully without crashing.
---"""

from __future__ import annotations
from pathlib import Path
import sys


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

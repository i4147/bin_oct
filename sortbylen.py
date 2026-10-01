#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that reads lines from a text file and sorts them by their character length, writing the result back to the same file in place.
It should use a helper function `read_lines` imported from a local module `dh` to load the file's lines while preserving line endings, and expose a `sort_by_length` function that sorts a list of strings by length with an optional reverse flag.
The script should accept the file path as a command-line argument and support an optional `-r` flag to sort in descending (reverse) order instead of ascending; if no path is provided, it should print a usage message and exit with status code 1.
After sorting and overwriting the file, it should print a confirmation message showing the filename and whether reverse order was used."""

import sys
from pathlib import Path
from dh import read_lines


def sort_by_length(lines: list[str], reverse: bool = False) -> list[str]:
    return sorted(lines, key=len, reverse=reverse)


if __name__ == "__main__":
    args = sys.argv[1:]
    reverse = False
    if "-r" in args:
        reverse = True
        args.remove("-r")
    if not args:
        print("Usage: python script.py [-r] <path>")
        sys.exit(1)
    path = Path(args[0].strip())
    lines = read_lines(path, ke=True)
    sorted_lines = sort_by_length(lines, reverse=reverse)
    path.write_text("".join(sorted_lines), encoding="utf8")
    print(f"{path.name} updated (reverse={reverse})")

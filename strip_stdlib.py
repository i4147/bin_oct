#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python command-line script that cleans up a requirements.txt-style file by removing entries that correspond to Python standard library modules, using a predefined STDLIB set imported from a module named "dh".
The script should accept the requirements file path as a command-line argument, read the file line by line while skipping blank lines and comments (lines starting with "#"), and normalize each package name by trimming whitespace, converting to lowercase, and replacing hyphens with underscores.
After filtering out any names found in STDLIB, it should overwrite the original file with the remaining package names (one per line, newline-terminated) and print a message reporting how many packages were removed."""

import sys
from pathlib import Path
from dh import STDLIB
def read_requirements(filename) -> list[str]:
    req_file = Path(filename)
    with Path(req_file).open(encoding="utf-8") as f:
        return [
            line.strip().replace("-", "_").lower()
            for line in f
            if line.strip() and not line.startswith("#")
        ]
def strip_stdlib(fname: str) -> None:
    lines = read_requirements(fname)
    new_lines = [line for line in lines if line not in STDLIB]
    Path(fname).write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    removed = len(lines) - len(new_lines)
    print(f"Removed {removed} packages")
if __name__ == "__main__":
    fn = sys.argv[1]
    strip_stdlib(fn)
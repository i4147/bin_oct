#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line tool for listing the most recently modified files in the current working directory. By default, it should list the top-level entries (files and directories) of the current folder, and when a recursive flag is provided, it should scan all files in the directory tree beneath the current folder. The user should be able to specify how many entries to display, with a default of 10.
The tool should skip symbolic links and any items located inside version-control or cache folders such as `.git` and `__pycache__`, regardless of how deeply nested they are.
Results should be ordered by modification time so that the least recently modified items appear first, with the list limited to the requested count. The output should begin with a short header line indicating how many entries are shown, followed by one line per item containing its last-modified timestamp in a human-readable date and time format and its path relative to the current folder.
Handle invalid or missing numeric arguments gracefully by falling back to the default count, and ensure the script runs cleanly without crashing when encountering files whose metadata cannot be read. The script should be self-contained, readable, and easy to run from any terminal inside the target directory.
---"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import sys
from dh import get_file_age

EXCLUDED_DIRS = {".git", "__pycache__"}


def format_time(ts: float | str) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    cwd = Path.cwd()
    files = []
    opt = "-r" if len(sys.argv) > 1 else "-g"
    N = int(sys.argv[2].strip()) if len(sys.argv) > 2 else 10
    if opt == "-g":
        for p in cwd.glob("*"):
            if p.is_symlink() or any(part in EXCLUDED_DIRS for part in p.parts):
                continue
            if p.is_file() or p.is_dir():
                files.append(p)
    elif opt == "-r":
        for p in cwd.rglob("*"):
            if p.is_symlink() or any(part in EXCLUDED_DIRS for part in p.parts):
                continue
            if p.is_file():
                files.append(p)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=False)
    print(f"\nTop {N} fresh files:\n")
    for f in files[:N]:
        mtime = get_file_age(f)
        print(f"{format_time(mtime)}  -  {f.relative_to(cwd)}")


if __name__ == "__main__":
    raise SystemExit(main())

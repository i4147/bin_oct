#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that lists the most recently modified files in the current directory, showing each file's modification timestamp alongside its relative path.
It should accept an optional command-line flag to switch between scanning only the top-level directory (default) and recursively scanning all subdirectories, skipping symlinks and any paths under ".git" or "__pycache__".
It should also accept an optional numeric argument controlling how many of the newest files to display (default 10), sort the collected files by modification time, and rely on an external helper function to retrieve each file's age/timestamp before printing a formatted "Top N fresh files" report to stdout."""

from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
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

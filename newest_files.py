#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that lists the most recently created files (or files and directories) in the current working directory, excluding ".git" and "__pycache__" paths and symlinks.
It should accept an optional first argument to switch between a shallow glob scan (default) and a recursive rglob scan, and an optional second argument specifying how many results to display (default 20).
The script sorts matched entries by creation time descending and prints each entry's formatted timestamp alongside its path relative to the current directory, preceded by a header showing the count of results being shown."""

from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path

EXCLUDED_DIRS = {".git", "__pycache__"}
N = 10


def format_time(ts) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def main() -> None:
    cwd = Path.cwd()
    files = []
    opt = "-r" if len(sys.argv) > 1 else "-g"
    N = int(sys.argv[2].strip()) if len(sys.argv) > 2 else 20
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
    files.sort(key=lambda f: f.stat().st_ctime, reverse=True)
    print(f"\nTop {N} oldest files (excluding .git & __pycache__):\n")
    for f in files[:N]:
        mtime = f.stat().st_ctime
        print(f"{format_time(mtime)}  -  {f.relative_to(cwd)}")


if __name__ == "__main__":
    raise SystemExit(main())

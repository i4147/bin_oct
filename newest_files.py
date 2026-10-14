#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that lists the most recently created files and folders in the current working directory, with an optional recursive mode and a configurable number of results. The script should be run from the command line and should behave as follows:
- By default, it examines only the top level of the current directory and reports both files and subdirectories. When a command-line flag indicates recursive mode, it scans every file within the current directory and all of its nested subdirectories, reporting only files.
- An optional numeric argument sets how many entries to display; if no count is supplied, it shows a sensible default of 20 entries.
- Results are ordered by file creation time, with the newest entries first, and the output is limited to the requested count.
- Ignore symbolic links entirely, and exclude any path that lies within version-control or Python cache directories (such as `.git` and `__pycache__`).
- Print a short heading to the console that states how many entries are shown and notes the excluded directories, followed by one line per entry showing its creation timestamp in a human-readable `YYYY-MM-DD HH:MM:SS` format and its path relative to the current directory.
- Handle missing or unreadable files gracefully without crashing, and validate that the count argument is a positive integer, printing a clear usage message when input is invalid.
- Keep the script self-contained, runnable with a standard Python 3 interpreter, and include a brief usage description printed when the script is invoked incorrectly.
---"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import sys

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

#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script that lists the most recently modified files in the current working directory. Reproduce these behaviors exactly:

**Purpose and invocation**
- Run as an executable with a Termux-style shebang (`#!/data/data/com.termux/files/usr/bin/env python`). Begin the file with `from __future__ import annotations`.
- Use only the standard library plus one external helper: `get_file_age` imported from a local module named `dh`. That helper takes a `Path` and returns a timestamp (a float epoch value or a string) for the file's age/modification time. Use it for the displayed timestamp, but sort by `stat().st_mtime`.

**Arguments**
- Mode selection: if there is at least one command-line argument (any value), mode is recursive `-r`; otherwise mode is `-g` (top-level only).
- Count N: if a second argument (`sys.argv[2]`) exists, parse it with `int()` after stripping whitespace; otherwise N defaults to 10. Do not add extra validation beyond what `int()` naturally raises.

**Collection logic**
- Define a module-level constant set `EXCLUDED_DIRS` containing `.git` and `__pycache__`.
- Base directory is `Path.cwd()`.
- `-g` mode: iterate `glob("*")` on the current directory (non-recursive). Include both files and directories.
- `-r` mode: iterate `rglob("*")` recursively. Include only regular files (not directories).
- In both modes, skip any path that is a symbolic link, and skip any path where any component of `p.parts` is in `EXCLUDED_DIRS`.
- Sort the collected list ascending by `stat().st_mtime` (oldest first).

**Output**
- Print a header line in the form: a blank line, then `Top N fresh files:`, then a blank line (N is the parsed count).
- For each of the first N entries in the sorted list (i.e., the oldest N in ascending order, as implemented), obtain the timestamp via `get_file_age(path)`, format it with a helper `format_time(ts)` that returns `datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")`, and print a line: `<formatted time>  -  <path relative to cwd>` with two spaces on each side of the hyphen.

**Structure**
- Put the logic in a `main() -> None` function, with type hints (`ts: float | str` for `format_time`).
- Entry point: `if __name__ == "__main__":` calling `raise SystemExit(main())`.

**Error handling and edge cases**
- No explicit try/except; let exceptions (invalid N, missing `dh` module, permission errors on stat) propagate.
- If there are fewer files than N, print all of them without error.
- If the directory is empty, print only the header.
- Symlinks are excluded entirely, including symlinked directories in recursive mode.

**Usage notes**
- Run from the directory to inspect; output paths are relative to that directory.
- Example invocations: `python script.py` (top-level, default 10), `python script.py x 5` (recursive, 5 entries).
---"""

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

#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained Python 3 command-line script (intended for Termux on Android, with a `#!/data/data/com.termux/files/usr/bin/env python` shebang and `from __future__ import annotations` at the top) that lists the most recently created files under the current working directory.

Behavior requirements:

**Purpose and arguments**
- Use only the standard library: `sys`, `datetime`, and `pathlib`. No third-party dependencies.
- Operate on the current working directory at runtime.
- Mode selection: if there is at least one command-line argument (`len(sys.argv) > 1`), use recursive mode; otherwise use a non-recursive "global" mode.
  - Recursive mode is selected by any first argument (the script does not check its literal value).
  - Non-recursive mode is selected when no arguments are given.
- An optional second argument (`sys.argv[2]`) specifies the count N of files to display, parsed as an integer after stripping whitespace. If absent, N defaults to 20. Note that a module-level constant N is defined as 10, but `main()` reassigns N locally, so the effective default is 20 and the printed header uses the effective N.
- A non-integer second argument will raise a `ValueError` (no special handling is required beyond what naturally occurs, but the implementation should not add extra validation unless it is clearly harmless).

**Collection logic**
- Define an excluded-directory set containing `.git` and `__pycache__`. Skip any path where any component of `p.parts` matches one of these names.
- Skip all symbolic links (`is_symlink()`).
- Non-recursive mode: iterate `cwd.glob("*")` (top level only). Include entries that are files or directories (directories are included in this mode).
- Recursive mode: iterate `cwd.rglob("*")` (all depths). Include only regular files (`is_file()`), not directories.
- Note: the exclusion check uses `p.parts`, which contains the full path, so an excluded name anywhere in the absolute path will exclude the entry.

**Sorting and output**
- Sort collected paths by file status change/creation timestamp `st_ctime` in descending order (newest first). Note this is `st_ctime`, which is inode change time on Unix-like systems, not necessarily true creation time.
- Print a header line preceded by a newline, in the form: `Top {N} oldest files (excluding .git & __pycache__):` followed by a blank line.
- Note the header says "oldest" although the list is sorted newest-first; reproduce the header text exactly and preserve the descending sort.
- For the first N entries, print one line per entry: the timestamp formatted as `YYYY-MM-DD HH:MM:SS` (local time via `datetime.fromtimestamp`), then two spaces, a hyphen, two spaces, then the path relative to the cwd.
- Reuse a small helper function `format_time(ts)` that returns the formatted string.
- Stat calls may be repeated; correctness does not depend on caching.

**Entry point**
- `main()` returns `None`. The `if __name__ == "__main__":` guard calls `raise SystemExit(main())`, so the process exits with status 0 on success.
- Use type hints (`-> str`, `-> None`) and `from __future__ import annotations`.

**Error handling and edge cases**
- No explicit try/except blocks; errors such as permission failures during stat or a non-integer N propagate as uncaught exceptions.
- An empty directory prints only the header and no file lines.
- Files that disappear between globbing and stat may raise exceptions.
- Symlinked files and directories are excluded entirely, including symlinked directories that would otherwise be traversed.

**Output format**
- Only the header and the file lines are printed; there is no other diagnostic output.
---"""

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

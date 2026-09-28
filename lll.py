#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively lists all files under the current working directory, sorted by modification time from newest to oldest, while skipping directories and excluded folders such as .mypy_cache, .ruff_cache, .git, and __pycache__.
For each file it should print the truncated filename, a formatted file size (using helper functions fsz and gsz from a module named dh, with special handling and padding for the size string width), and the last-modified time in HH:MM format, all rendered with ANSI escape codes for colored, blinking terminal output.
Symlinks should be detected and labeled distinctly with a "symlink" marker and a different color instead of showing a computed size.
The script runs only when executed directly (via the __main__ guard) and outputs directly to stdout with no return value or file writing."""

import datetime
from pathlib import Path
from dh import fsz, gsz

EXCLUDED = {".mypy_cache", ".ruff_cache", ".git", "__pycache__"}
if __name__ == "__main__":
    cwd = Path.cwd()
    for path in sorted(cwd.rglob("*"), key=lambda e: e.stat().st_mtime, reverse=True):
        if any(pat in path.parts for pat in EXCLUDED):
            continue
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%H:%M")
        if path.is_dir():
            continue
        elif path.is_symlink():
            sz = " \x1b[05;95msymlink "
        else:
            sz = str(fsz(gsz(path)))
            if len(sz) == 7:
                sz = "  " + sz
            if len(sz) == 8:
                sz = " " + sz
        if path.is_symlink():
            print(f"\x1b[05;95m{path.name[:24]:25}\x1b[0m", end=" ")
        else:
            print(f"\x1b[05;94m{path.name[:24]:25}\x1b[0m", end=" ")
        print(f"\x1b[05;96m{sz}\x1b[0m", end=" ")
        print(f"\x1b[05;93m{mtime}\x1b[0m")

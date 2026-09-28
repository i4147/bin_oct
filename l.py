#!/data/data/com.termux/files/home/.local/bin/python
"""Write a Python script that recursively lists all files under the current working directory, sorted by modification time, while skipping common cache/VCS folders such as .mypy_cache, .ruff_cache, .git, and __pycache__.
For each file it should print the truncated filename, a right-aligned human-readable file size (using helper functions fsz and gsz from a local dh module), and the modification time formatted as HH:MM, all rendered with ANSI color codes for styling.
Directories should be skipped from output, while symlinks should be specially highlighted in a distinct color and labeled as "symlink" instead of showing a size.
The script should run as a standalone command-line tool when executed directly."""

import datetime
from pathlib import Path
from dh import fsz, gsz

EXCLUDED = {".mypy_cache", ".ruff_cache", ".git", "__pycache__"}
if __name__ == "__main__":
    cwd = Path.cwd()
    for path in sorted(cwd.rglob("*"), key=lambda e: e.stat().st_mtime):
        if any(pat in path.parts for pat in EXCLUDED):
            continue
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%H:%M")
        if path.is_dir():
            continue
        elif path.is_symlink():
            sz = " \x1b[05;95msymlink "
        else:
            sz = str(fsz(gsz(path)))
            match len(sz):
                case 3:
                    sz = "      " + sz
                case 4:
                    sz = "     " + sz
                case 5:
                    sz = "    " + sz
                case 6:
                    sz = "   " + sz
                case 7:
                    sz = "  " + sz
                case 8:
                    sz = " " + sz
        if path.is_symlink():
            print(f"\x1b[05;95m{path.name[:24]:25}\x1b[0m", end=" ")
        else:
            print(f"\x1b[05;94m{path.name[:24]:25}\x1b[0m", end=" ")
        print(f"\x1b[05;96m{sz}\x1b[0m", end=" ")
        print(f"\x1b[05;93m{mtime}\x1b[0m")

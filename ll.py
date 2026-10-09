#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python 3.12 script intended to run under Termux (shebang `#!/data/data/com.termux/files/usr/bin/python3.12`) that acts as a custom directory listing utility (an `ls`-like tool) for the current working directory.

Purpose and behavior:
- The script lists all entries (files and directories, including hidden-pattern matches via `* glob) in the current working directory (`Path.cwd()`), sorted by file size.
- It accepts an optional command-line flag `-r` (checked via `sys.argv`) to reverse the sort order (descending vs ascending by size).
- It separates entries into two groups: directories and non-directory items (files, symlinks, etc.), processing/printing them potentially with different formatting (directories likely shown differently from files, e.g., with a trailing marker or distinct coloring).
- For each non-directory entry, it computes the creation time (`st_ctime`) formatted as `HH:MM`, and determines if the entry is a symlink to apply special formatting (e.g., ANSI escape codes for color/blink to highlight broken or symlinked files).
- Include a helper function `fsz(sz)` that converts a raw byte size (integer/float) into a human-readable string using binary units (B, KB, MB, GB, TB), comput via bit-length math, and returning a formatted string like `"0 B"`, `"4 KB"`, etc. (always using absolute value and integer truncation).
- Include a helper function `gsz(path)` that recursively calculates the total size in bytes of a given path: returns 0 if the path doesn't exist; returns the file's own size if it's a file; if it's a directory, it iterates over its entries using `os.scandir`, skips symlinks and nonexistent entries, sums file sizes directly, and recurses into subdirectories to accumulate their sizes — with OSError handling to skip inaccessible entries gracefully.
- The script should gracefully skip any path that no longer exists during iteration (e.g., race conditions where files are deleted mid-listing).
- Output should use ANSI escape sequences for terminal styling (e.g., colors, blinking text) to visually distinguish file types (such as symlinks) in the printed listing.
- No external dependencies beyond the Python standard library (`datetime`, `sys`, `os.scandir`, `pathlib.Path`).
- The script is meant to be run directly as an executable (guarded by `if __name__ == "__main__":`) with no other inputs besides the optional `-r` flag, and it prints the formatted directory listing directly to stdout.
---
LiveDoc: https://felo.ai/zh-Hans/livedoc/HbgEvfUpatXJZ4d43M8Z9H"""

from __future__ import annotations
import datetime
from os import scandir as _scandir
from pathlib import Path
import sys


REVERSE = "-r" in sys.argv


def fsz(sz: float) -> str:
    sz = abs(int(sz))
    units = ("", "K", "M", "G", "T")
    if sz == 0:
        return "0 B"
    i = min(int(int(sz).bit_length() - 1) // 10, len(units) - 1)
    sz /= 1024**i
    return f"{int(sz)} {units[i]}B"


def gsz(path: str | Path) -> int:
    path = Path(path)
    total_size = 0
    if not path.exists():
        return 0
    if path.is_file():
        try:
            total_size = path.stat().st_size
        except OSError:
            return 0
    elif path.is_dir():
        for entry in _scandir(path):
            try:
                if Path(entry.path).is_symlink() or not Path(entry.path).exists():
                    continue
                if entry.is_file():
                    total_size += entry.stat().st_size
                elif entry.is_dir():
                    total_size += gsz(entry.path)
            except OSError:
                continue
    return total_size


if __name__ == "__main__":
    cwd = Path.cwd()
    dirz = []
    otherz = []
    sz = ""
    for path in sorted(cwd.glob("*"), key=lambda e: e.stat().st_size, reverse=REVERSE):
        if not path.exists():
            continue
        if path.is_dir():
            dirz.append(path)
        else:
            otherz.append(path)
    for f in otherz:
        ctime = datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%H:%M")
        if f.is_symlink():
            print(f"\x1b[05;95m{f.name[:24]:25}\x1b[0m", end=" ")
        else:
            sz = str(fsz(gsz(f)))
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
            print(f"\x1b[05;92m{f.stem[:20] + f.suffix:25}\x1b[0m", end=" ")
        print(f"\x1b[05;96m{sz}\x1b[0m", end=" ")
        print(f"\x1b[05;93m{ctime}\x1b[0m")
    for dr in sorted(dirz):
        ctime = datetime.datetime.fromtimestamp(dr.stat().st_ctime).strftime("%H:%M")
        sz = str(fsz(gsz(dr)))
        if len(sz) == 7:
            sz = "  " + sz
        if len(sz) == 8:
            sz = " " + sz
        print(f"\x1b[05;94m{dr.name[:24]:25}\x1b[0m", end=" ")
        print(f"\x1b[05;96m{sz}\x1b[0m", end=" ")
        print(f"\x1b[05;93m{ctime}\x1b[0m")

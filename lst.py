#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that lists all files, directories, and symlinks in the current working directory, sorted by modification time (oldest to newest).
For each entry, it should print the name (truncated to 24 characters) in blue, followed by its size in cyan (formatted and right-aligned using helper functions from a custom "dh" module, with symlinks shown as " symlink " instead of a size), and finally the last-modified time in "HH:MM" format in yellow.
It relies on custom utilities cprint (colored print), fsz (format size), and gsz (get size) imported from a local module named dh."""

import datetime
from pathlib import Path
from dh import cprint, fsz, gsz

if __name__ == "__main__":
    cwd = Path.cwd()
    for path in sorted(cwd.glob("*"), key=lambda e: e.stat().st_mtime):
        mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime).strftime("%H:%M")
        if path.is_symlink():
            sz = " symlink "
        elif path.is_file() or path.is_dir():
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
        cprint(f"{path.name[:24]:25}", "blue", end=" ")
        cprint(f"{sz}", "cyan", end=" ")
        cprint(f"{mtime}", "yellow")

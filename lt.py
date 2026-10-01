#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python script that lists the contents of the current working directory in a colorized, blinking terminal output, using helper functions `fsz` and `gsz` from a local `dh` module to compute human-readable and raw sizes.
It should separate directories from files/symlinks, sort all entries by creation time (newest first), and print files/symlinks before directories, showing each entry's truncated name (max 24 chars), formatted size (right-padded based on digit count), and creation timestamp in "MM/DD/YY-HH:MM" format.
Symlinks should be highlighted in magenta, regular files in green, directories in blue, sizes in cyan, and timestamps in yellow, all using ANSI escape codes with blink formatting."""

import datetime
from pathlib import Path
from dh import fsz, gsz

if __name__ == "__main__":
    cwd = Path.cwd()
    dirz = []
    otherz = []
    for path in sorted(cwd.glob("*"), key=lambda e: e.stat().st_ctime, reverse=True):
        if path.is_dir():
            dirz.append(path)
        else:
            otherz.append(path)
    for f in otherz:
        ctime = datetime.datetime.fromtimestamp(f.stat().st_ctime).strftime("%D-%H:%M")
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
            print(f"\x1b[05;92m{f.name[:24]:25}\x1b[0m", end=" ")
        print(f"\x1b[05;96m{sz}\x1b[0m", end=" ")
        print(f"\x1b[05;93m{ctime}\x1b[0m")
    for dr in dirz:
        ctime = datetime.datetime.fromtimestamp(dr.stat().st_ctime).strftime("%D-%H:%M")
        sz = str(fsz(gsz(dr)))
        if len(sz) == 7:
            sz = "  " + sz
        if len(sz) == 8:
            sz = " " + sz
        print(f"\x1b[05;94m{dr.name[:24]:25}\x1b[0m", end=" ")
        print(f"\x1b[05;96m{sz}\x1b[0m", end=" ")
        print(f"\x1b[05;93m{ctime}\x1b[0m")

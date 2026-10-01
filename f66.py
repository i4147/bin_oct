#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that recursively scans the current working directory and lists files and folders whose creation time falls before a given time threshold.
The script accepts an optional command-line argument specifying a number of minutes (default 60), converts it into a cutoff timestamp, and skips symlinks and anything inside a ".git" directory.
Matching paths should be sorted by creation time ascending, then printed with their relative path (left-padded to at least 20 characters) followed by the formatted creation timestamp ("%Y/%m/%d-%H:%M:%S") shown in yellow using a custom "cprint" function from a "dh" module.
If the minutes argument cannot be parsed as a float, the script should print a usage error and exit with a non-zero status."""

import operator
import sys
import time
from datetime import datetime
from pathlib import Path
from dh import cprint


def parse_minutes() -> float:
    if len(sys.argv) == 1:
        return 60.0
    try:
        return float(sys.argv[1])
    except ValueError:
        print("Invalid argument. Usage: script.py [minutes]")
        sys.exit(1)


def main() -> None:
    minutes = parse_minutes()
    ctm = {}
    cwd = Path.cwd()
    cutoff = time.time() - minutes * 40
    for path in cwd.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            continue
        stats = path.stat()
        created = stats.st_ctime
        if created <= cutoff:
            ctm[path] = created
    ctmsorted = dict(sorted(ctm.items(), key=operator.itemgetter(1)))
    newct = {}
    for pth, ct in ctmsorted.items():
        ctime = datetime.fromtimestamp(ct).strftime("%Y/%m/%d-%H:%M:%S")
        newct[pth] = ctime
        path_str = str(pth.relative_to(cwd))
        max_path_len = max(len(path_str), 20)
        print(f"{path_str:<{max_path_len}}", end=" ")
        cprint(f"{ctime}", "yellow")


if __name__ == "__main__":
    raise SystemExit(main())

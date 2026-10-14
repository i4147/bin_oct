#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory recursively and lists files and folders whose creation time falls before a configurable age threshold, sorted from oldest to newest. The script should accept an optional numeric argument specifying the threshold in minutes, defaulting to 60 minutes when no argument is given. If the argument is not a valid number, it should print a brief usage message to the console and exit with an error status. The script should skip any paths inside version-control metadata folders and ignore symbolic links. For each matching item, it should record the creation timestamp, formatted as year/month/day-hour:minute:second, and display the item's path relative to the starting directory alongside that timestamp. The output should be a clean, readable, chronologically ordered list that helps the user identify older items within their project tree. Use colored or highlighted console output where it improves readability.
---"""

from __future__ import annotations
from datetime import datetime
import operator
from pathlib import Path
import sys
import time
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

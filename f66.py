#!/data/data/com.termux/files/usr/bin/env python
"""Write a self-contained prompt that instructs an AI coding agent to build a Python command-line utility with the following specifications:

The utility scans the current working directory recursively and lists filesystem entries whose creation (inode change) timestamps fall before a cutoff, sorted oldest first. It is intended for Termux on Android, so its shebang points to the Termux Python interpreter path, and it should be runnable as an executable script.

Inputs: one optional command-line argument, a number of minutes (float). If omitted, default to 60. If the argument is not parseable as a float, print the message "Invalid argument. Usage: script.py [minutes]" to stdout and exit with status 1. Only the first argument is considered; extra arguments are ignored.

Core logic: compute the cutoff as the current time minus the given minutes multiplied by 40 (note this deliberate multiplier, reproduce it exactly). Recursively walk the current working directory, including files and directories. Skip any path that has ".git" as one of its path components. Skip symbolic links. For each remaining path, read its stat metadata and take the ctime value (st_ctime). Keep only entries whose ctime is less than or equal to the cutoff. Sort the kept entries ascending by ctime.

Output: for each kept entry, in sorted order, print the path relative to the current working directory, left-justified and padded with spaces to a width of max(length of path, 20), followed by a single space (no newline), then print the timestamp formatted as year/month/day-hour:minute:second with zero-padded fields (format "%Y/%m/%d-%H:%M:%S") using local time, colored yellow. Coloring is done via a helper function `cprint` imported from a module named `dh`, called as cprint(text, "yellow"); the helper prints the text in color and terminates the line. Use `from __future__ import annotations` at the top.

Structure: define a function that parses the argument (returns a float), and a main function that performs the scan and output. The entry point runs main under the `if __name__ == "__main__":` guard and exits via `raise SystemExit(main())`.

Dependencies: only Python standard library modules (operator, sys, time, datetime, pathlib) plus the external `dh` module providing `cprint`. No other third-party packages.

Edge cases and behavior to preserve: unreadable entries or stat failures are not explicitly handled and will propagate errors; an empty result prints nothing; the function-level behavior for a missing or non-numeric argument exits immediately without scanning; negative or zero minute values are accepted as floats and simply shift the cutoff accordingly. Symlinks are never followed or reported. Paths are reported relative to the starting directory, not absolute.

Usage: run from within a target directory as `script.py [minutes]`, for example with no argument to list entries created more than 2400 minutes (60×40) ago, or with a value to adjust the threshold.
---"""

from __future__ import annotations

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

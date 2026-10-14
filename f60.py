#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that scans the current working directory and reports on its non-hidden entries based on their creation and modification times, relative to a time window the user specifies in minutes (defaulting to 60 if no accept a single optional numeric argument for the time window, and if the argument is not a valid number it should print a brief usage message (e.g., "Usage: script.py [minutes]") and exit with a non-zero status.
The script should examine only the top-level items in the current directory, skip any version-control metadata folders and symbolic links, and select entries whose creation time falls at or before the cutoff or whose modification time falls at or after the cutoff. Selected entries should be ordered chronologically by their creation time, and the script should then produce a clear, aligned, human-readable listing of the results, showing each entry's name along with its creation and modification timestamps in a readable date-time format. The output column widths should adapt to the longest entry name, with a sensible minimum width so the table stays neatly formatted. The script should handle the case where no entries match gracefully and print an appropriate message. Keep the design simple, reliable, and cross-platform, and make sure the script runs as a standalone command-line tool with no external dependencies beyond the Python standard library.
---"""

from __future__ import annotations
from datetime import datetime
import operator
from pathlib import Path
import sys
import time


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
    max_path_string = 20
    cutoff = time.time() - minutes * 40
    for path in cwd.glob("*"):
        if ".git" in path.parts:
            continue
        if path.is_symlink():
            continue
        stats = path.stat()
        created = stats.st_ctime
        modified = stats.st_mtime
        pathstr = str(path.name)
        max_path_string = max(len(pathstr), 20)
        if created <= cutoff or modified >= cutoff:
            ctm[path] = created
    ctmsorted = dict(sorted(ctm.items(), key=operator.itemgetter(1)))
    newct = {}
    for pth, ct in ctmsorted.items():
        ctime = datetime.fromtimestamp(ct).strftime("%Y/%m/%d-%H:%M:%S")
        newct[pth] = ctime
        print(f"\x1b[05;96m{Path(pth).name[:19]:<{max_path_string}} \x1b[05;93m{ctime}\x1b[0m")


if __name__ == "__main__":
    raise SystemExit(main())

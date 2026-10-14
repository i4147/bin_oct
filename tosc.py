#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that acts as a command-line file collector and mover. It should accept one or more file paths or glob patterns as arguments, plus an optional fl file that contains a list of paths or patterns (one per line, ignoring blank lines). When run with no arguments, it should print a short usage message to standard error and exit with a non-zero status.
For each resolved input, the script should locate the matching files (supporting recursive glob matching, and treating an existing literal path as a direct match) and ignore anything that is not a regular file. It should then move or copy each collected file into a fixed destination folder located in the user's home directory under a nested "isaac/may/scripts" path, creating that folder if it does not already exist. If a file with the same name already exists at the destination, the script must avoid overwriting it by generating a unique alternative name.
The script should report clearly to the user what it did: the number of files processed, each destination written, and any paths that matched nothing or failed, with errors written to standard error rather than halting the entire run. Handle missing list files and missing flag arguments gracefully with helpful error messages and a non-zero exit code. Use the command line as the sole interface, and keep the behavior deterministic so that repeated runs with the same inputs produce predictable results.
---"""

from __future__ import annotations
import glob
from pathlib import Path
import shutil
import sys
from dh import unique_path

h = Path.home() / "isaac" / "may" / "scripts"


def i(a):
    g = Path(a)
    if g.exists():
        return [g]
    k = glob.glob(a, recursive=True)
    return [Path(f) for f in k if Path(f).is_file()]


def j():
    args = sys.argv[1:]
    if not args:
        print(f"usage: {Path(sys.argv[0]).name} [-f LISTFILE] [FILE ...]", file=sys.stderr)
        raise SystemExit(1)
    patterns = []
    listfile = None
    k = 0
    while k < len(args):
        a = args[k]
        if a == "-f":
            if k + 1 >= len(args):
                print("-f requires an argument", file=sys.stderr)
                raise SystemExit(1)
            listfile = args[k + 1]
            k += 2
            continue
        patterns.append(a)
        k += 1
    if listfile is not None:
        try:
            with open(listfile) as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except OSError as e:
            print(f"cannot read {listfile}: {e}", file=sys.stderr)
            raise SystemExit(1)
    if not patterns:
        print("no files to move", file=sys.stderr)
        raise SystemExit(1)
    d = []
    for a in patterns:
        e = i(a)
        if not e:
            print(f"no matches: {a}", file=sys.stderr)
            continue
        d.extend(e)
    for c in d:
        b = h / c.name
        if b.exists():
            b = unique_path(b)
        shutil.move(str(c), str(b))
        print(f"{c.name} --> {b.name}")


if __name__ == "__main__":
    raise SystemExit(j())

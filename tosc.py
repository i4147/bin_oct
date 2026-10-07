#!/data/data/com.termux/files/usr/bin/env python
"""Write a Python command-line script that moves one or more files into a fixed destination folder (~/isaac/may/scripts).
It should accept file paths and/or glob patterns as command-line arguments, expanding each pattern via glob.glob (recursively) and filtering to existing files, printing a warning to stderr for any argument that matches nothing.
For each resolved file it should move it into the destination directory using shutil.move, relying on a helper function unique_path (imported from a module named dh) to rename the target if a file with the same name already exists there, and print a line showing the original filename and the final destination filename.
If no arguments are provided, it should print a usage message to stderr and exit with status 1."""

from __future__ import annotations
import glob
import shutil
import sys
from pathlib import Path
from dh import unique_path

dest = Path.home() / "isaac" / "may" / "scripts"


def expand(arg: str) -> list[Path]:
    p = Path(arg)
    if p.exists():
        return [p]
    matches = glob.glob(arg, recursive=True)
    return [Path(m) for m in matches if Path(m).is_file()]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"usage: {Path(sys.argv[0]).name} FILE [FILE ...]", file=sys.stderr)
        raise SystemExit(1)
    files: list[Path] = []
    for arg in sys.argv[1:]:
        found = expand(arg)
        if not found:
            print(f"no matches: {arg}", file=sys.stderr)
            continue
        files.extend(found)
    for fn in files:
        dest_path = dest / fn.name
        if dest_path.exists():
            dest_path = unique_path(dest_path)
        shutil.move(str(fn), str(dest_path))
        print(f"{fn.name} --> {dest_path.name}")


if __name__ == "__main__":
    raise SystemExit(main())

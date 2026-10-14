#!/data/data/com.termux/files/usr/bin/python
"""Write a Python script that lists entries in the current working directory whose names contain a user-supplied search text, printing each match as a sorted, bulleted list. The script should accept a single search term as a command-line argument and an optional flag that changes how symbolic links are handled: by default, symbolic links are excluded from the results, but when the flag is provided they are included. Each included symbolic link should be displayed along with the path it points to (fully resolved), while regular files and directories are displayed by name only. If no search term is provided, the script should handle that case gracefully with a brief usage message. The script should only inspect the top level of the current directory (no recursion) and should exit cleanly with a status code when finished.
---"""

from __future__ import annotations
from pathlib import Path
import sys


def main() -> None:
    cwd = Path.cwd()
    args = sys.argv[1:]
    skip_symlinks = True
    search_pattern = None
    for arg in args:
        if arg == "-s":
            skip_symlinks = False
        else:
            search_pattern = arg.strip()
    found = []
    for path in cwd.glob("*"):
        if search_pattern in path.name:
            if skip_symlinks and path.is_symlink():
                continue
            found.append(path)
    for k in sorted(found):
        if k.is_symlink():
            print(f"  - {k.name} -> {k.resolve()}")
        else:
            print(f"  - {k.name}")


if __name__ == "__main__":
    raise SystemExit(main())

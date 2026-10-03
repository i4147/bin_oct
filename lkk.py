#!/data/data/com.termux/files/usr/bin/python3.12
"""Write a Python command-line script that searches the current working directory for files or folders whose names contain a given substring, then prints the matches sorted alphabetically.
It should accept the search pattern as a command-line argument and support an optional "-s" flag that, when present, includes symlinks in the results (by default symlinks are skipped).
For each match printed, regular entries should be shown as " - name" while symlinks should be shown as " - name -> resolved_target_path".
Use pathlib for filesystem operations and sys.argv for argument parsing."""

from __future__ import annotations

import sys
from pathlib import Path


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

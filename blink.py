#!/data/data/com.termux/files/usr/bin/python3.12
"""
Write a Python script that recursively scans the current working directory for broken symbolic links (symlinks pointing to nonexistent targets), skipping any files inside ".git" directories.
For each broken symlink found, it should either delete it and print a confirmation message, or, if the script is run with a "-d" command-line flag (dry-run mode), simply print the file name without deleting it.
The script should use pathlib's Path.walk() for directory traversal and be structured with a "blink" function that performs the scan/cleanup and a "main" function that invokes it on the current directory, following the standard "if __name__ == '__main__'" entry point pattern.
"""

from __future__ import annotations
import sys
from pathlib import Path


def blink(directory: Path) -> None:
    for root, _, files in directory.walk():
        for f in files:
            fullpath = Path(root) / f
            if ".git" in fullpath.parts:
                continue
            if fullpath.is_symlink() and not fullpath.exists():
                if "-d" not in sys.argv:
                    fullpath.unlink()
                    print(f" - {f} removed.")
                else:
                    print(f" - {f} (rerun without -d to remove")


def main():
    cwd = Path.cwd()
    blink(cwd)


if __name__ == "__main__":
    raise SystemExit(main())
